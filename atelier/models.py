from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import time
from decimal import Decimal
import datetime

class Cliente(models.Model):
    nome = models.CharField(max_length=150, verbose_name="Nome Completo")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone/WhatsApp")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class CategoriaMaterial(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome

class Material(models.Model):
    
    UNIDADE_CHOICES = [
        ('metro', 'Metro'),
        ('unidade', 'Unidade'),
        ('rolo', 'Rolo'),
        ('quilo', 'Quilo'),
        ('grama', 'Grama'),
    ]
    
    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(CategoriaMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais')
    # Pode ser metro, unidade, rolo, etc.
    unidade_medida = models.CharField(max_length=20, choices=UNIDADE_CHOICES) 
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
    nome = models.CharField(max_length=100, verbose_name="Nome do Produto")
    descricao = models.TextField(blank=True, verbose_name="Descrição do Produto")
    
    # Armazena horas e minutos (ex: 04:30)
    tempo_trabalho_horas = models.TimeField(
        verbose_name="Tempo de Trabalho (Horas)",
        default=datetime.time(0, 0)
    )
    
    valor_hora_trabalho = models.DecimalField(max_digits=10, decimal_places=2, default=12.00, verbose_name="Hora de Trabalho (R$)")
    margem_lucro_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=50.0, verbose_name="Margem de Lucro (%)")
    desconto_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Desconto em Reais", verbose_name="Desconto (R$)")
    
    imagem_frente = models.ImageField(upload_to='produtos/', null=True, blank=True)
    imagem_lado = models.ImageField(upload_to='produtos/', null=True, blank=True)
    imagem_tras = models.ImageField(upload_to='produtos/', null=True, blank=True)
    
    # Campo para salvar o preço final calculado
    preco_final = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    # --- MÉTODO AUXILIAR PARA CONVERTER TEMPO PARA DECIMAL (Retornando Decimal) ---
    def get_tempo_em_decimal(self):
        """Converte o objeto TimeField (HH:MM) para Decimal de horas (ex: 4.5)"""
        if not self.tempo_trabalho_horas:
            return Decimal('0.0')
        
        horas = Decimal(str(self.tempo_trabalho_horas.hour))
        minutos = Decimal(str(self.tempo_trabalho_horas.minute))
        # Divide minutos por 60 para ter a fração decimal da hora
        return horas + (minutos / Decimal('60.0'))

    def get_custo_total_materiais(self):
        # Garante que o retorno seja sempre Decimal, mesmo que a lista esteja vazia
        soma = sum(item.subtotal_material() for item in self.materiais.all())
        return Decimal(str(soma)) if soma else Decimal('0.0')

    def calcular_e_salvar_preco(self):
        """Calcula e persiste o preço no banco de dados"""
        custo_materiais = self.get_custo_total_materiais()
        custo_mao_de_obra = self.get_tempo_em_decimal() * Decimal(str(self.valor_hora_trabalho))
        
        custo_total = custo_materiais + custo_mao_de_obra
        margem = Decimal(str(self.margem_lucro_percentual))
        
        # Preço com margem aplicada
        self.preco_final = custo_total * (Decimal('1') + (margem / Decimal('100')))
        self.save()

    def get_preco_final_sugerido(self):
        """Retorna o valor final com margem e desconto aplicado"""
        custo_materiais = self.get_custo_total_materiais()
        custo_mao_de_obra = self.get_tempo_em_decimal() * Decimal(str(self.valor_hora_trabalho))
        
        total_base = custo_materiais + custo_mao_de_obra
        margem = Decimal(str(self.margem_lucro_percentual))
        desconto = Decimal(str(self.desconto_valor))
        
        valor_com_margem = total_base * (Decimal('1') + (margem / Decimal('100')))
        return valor_com_margem - desconto

    def get_lucro_liquido(self):
        """Preço de venda menos custos reais (materiais + mão de obra)"""
        preco_venda = self.get_preco_final_sugerido()
        custo_materiais = self.get_custo_total_materiais()
        custo_mao_de_obra = self.get_tempo_em_decimal() * Decimal(str(self.valor_hora_trabalho))
        
        custo_total = custo_materiais + custo_mao_de_obra
        return preco_venda - custo_total
    
    def esta_vendido(self):
        return self.vendas.exists()

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
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas')

    def gerar_mensagem_whatsapp(self):
        nome = self.cliente.nome if self.cliente else "Cliente"
        texto = (
            f"Olá {nome}! "
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
    
def calcular_custo_mao_de_obra(self):
    if not self.tempo_trabalho_horas:
        return 0
    
    # Se tempo_trabalho_horas for um objeto time (HH:MM:SS)
    if isinstance(self.tempo_trabalho_horas, time):
        horas = self.tempo_trabalho_horas.hour
        minutos = self.tempo_trabalho_horas.minute
        tempo_decimal = horas + (minutos / 60)
        return tempo_decimal * self.valor_hora_trabalho
    
    # Se ainda for um decimal (caso não tenha migrado o banco)
    return float(self.tempo_trabalho_horas) * float(self.valor_hora_trabalho)