from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver



class Material(models.Model):
    nome = models.CharField(max_length=100)
    # Pode ser metro, unidade, rolo, etc.
    unidade_medida = models.CharField(max_length=20) 
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=1.0) # Alerta quando sobrar só 1 unidade

    @property
    def precisa_repor(self):
        return self.quantidade_estoque <= self.estoque_minimo

    def __str__(self):
        return self.nome
class EntradaMaterial(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='entradas')
    quantidade_adicionada = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario_na_compra = models.DecimalField(max_digits=10, decimal_places=2, help_text="Preço pago por unidade nesta compra")
    data_entrada = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Quando salvamos a entrada, atualizamos o estoque principal
        self.material.quantidade_estoque += self.quantidade_adicionada
        
        # 2. Atualizamos também o preço unitário do material para os próximos cálculos
        self.material.preco_unitario = self.preco_unitario_na_compra
        
        self.material.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Entrada: {self.material.nome} (+{self.quantidade_adicionada})"


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    tempo_trabalho_horas = models.DecimalField(max_digits=5, decimal_places=2)
    valor_hora_trabalho = models.DecimalField(max_digits=10, decimal_places=2, default=12.00)
    margem_lucro_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Desconto em Reais")
    imagem_frente = models.ImageField(upload_to='produtos/', null=True, blank=True)
    imagem_lado = models.ImageField(upload_to='produtos/', null=True, blank=True)
    imagem_tras = models.ImageField(upload_to='produtos/', null=True, blank=True)
    
    # Campo para salvar o preço final calculado
    preco_final = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    
    def calcular_e_salvar_preco(self):
        # Soma o custo de cada item da composição
        custo_materiais = sum(item.subtotal_material() for item in self.materiais.all())
        
        # Custo da mão de obra
        custo_mao_de_obra = self.tempo_trabalho_horas * self.valor_hora_trabalho
        
        # Preço Final com Margem
        custo_total = custo_materiais + custo_mao_de_obra
        self.preco_final = custo_total * (1 + (self.margem_lucro_percentual / 100))
        
        self.save()
        
        # Dentro da classe Produto no models.py
    def get_custo_total_materiais(self):
        return sum(item.subtotal_material() for item in self.materiais.all())

    def get_preco_final_sugerido(self):
        custo_materiais = self.get_custo_total_materiais()
        custo_mao_de_obra = self.tempo_trabalho_horas * self.valor_hora_trabalho
        total = custo_materiais + custo_mao_de_obra
        # Aplica margem e DEPOIS subtrai o desconto
        return (total * (1 + (self.margem_lucro_percentual / 100))) - self.desconto_valor

    def get_lucro_liquido(self):
        # O lucro real é o que sobra depois de pagar materiais e sua própria hora
        preco_venda = self.get_preco_final_sugerido()
        custo_materiais = self.get_custo_total_materiais()
        custo_mao_de_obra = self.tempo_trabalho_horas * self.valor_hora_trabalho
        
        return preco_venda - (custo_materiais + custo_mao_de_obra)
    
    def esta_vendido(self):
        return self.vendas.exists() # 'vendas' é o related_name que definimos no Model Venda

    def __str__(self):
        return self.nome

class ItemComposicao(models.Model):
    """ Esta tabela liga o Material ao Produto e define a quantidade """
    produto = models.ForeignKey(Produto, related_name='materiais', on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantidade_utilizada = models.DecimalField(max_digits=10, decimal_places=3) # Ex: 1.500 metros

    def subtotal_material(self):
        return self.quantidade_utilizada * self.material.preco_unitario
    
class Venda(models.Model):
    METODO_PAGAMENTO = [
        ('PIX', 'Pix'),
        ('CREDITO', 'Cartão de Crédito'),
        ('DEBITO', 'Cartão de Débito'),
        ('DINHEIRO', 'Dinheiro'),
    ]

    produto = models.ForeignKey('Produto', on_delete=models.CASCADE, related_name='vendas')
    data_venda = models.DateTimeField(default=timezone.now)
    valor_venda = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_PAGAMENTO)
    observacoes = models.TextField(blank=True, null=True)
    nome_cliente = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nome do Cliente")
    telefone_cliente = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="Ex: 51999999999 (Apenas números com DDD)",
        verbose_name="Telefone/WhatsApp"
    )

    def gerar_mensagem_whatsapp(self):
        texto = (
            f"Olá {self.nome_cliente}! "
            f"Segue o recibo da sua compra: {self.produto.nome}. "
            f"Valor: R$ {self.valor_venda:.2f}"
        )
        return texto

    def save(self, *args, **kwargs):   
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venda: {self.produto.nome} - {self.data_venda.strftime('%d/%m/%Y')}"
    
    
@receiver(post_save, sender=ItemComposicao)
def ajustar_estoque_no_salvamento(sender, instance, created, **kwargs):
    """
    Quando um material é adicionado a um produto, baixamos o estoque.
    Se for uma edição, compensamos a diferença.
    """
    if created:
        # Se o item acabou de ser criado, subtrai a quantidade total
        material = instance.material
        material.quantidade_estoque -= instance.quantidade_utilizada
        material.save()
    # Nota: Lógica de edição complexa pode ser adicionada aqui se necessário.

@receiver(post_delete, sender=ItemComposicao)
def devolver_estoque_na_delecao(sender, instance, **kwargs):
    """
    Se você deletar um item do produto (ou o produto inteiro), 
    o material volta para o estoque automaticamente.
    """
    material = instance.material
    material.quantidade_estoque += instance.quantidade_utilizada
    material.save()