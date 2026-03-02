from django import forms
import datetime
from .models import Produto, ItemComposicao, Material, Venda, EntradaMaterial, CategoriaMaterial, Cliente

# 1. Formulário de Materiais (Estoque)
class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['nome', 'unidade_medida', 'preco_unitario', 'quantidade_estoque', 'categoria']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'unidade_medida': forms.Select(attrs={'class': 'form-select'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade_estoque': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Aplica a classe form-control para todos os campos
            for field_name, field in self.fields.items():
                field.widget.attrs['class'] = 'form-control'
            
            # Opcional: Adicionar um placeholder amigável para o preço
            self.fields['preco_unitario'].widget.attrs['placeholder'] = '0.00'

# 2. Formulário Principal do Produto
class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'tempo_trabalho_horas', 'valor_hora_trabalho', 'margem_lucro_percentual', 'desconto_valor', 'imagem_frente', 'imagem_lado', 'imagem_tras']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control','rows': 2, 'style': 'resize:none;'}),
            
            # --- AJUSTE AQUI ---
            # TimeInput é o widget correto para TimeField
            'tempo_trabalho_horas': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time', 'step': '60'},
                format='%H:%M'
            ),
            # --------------------
            
            'valor_hora_trabalho': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'margem_lucro_percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'desconto_valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }        
# 3. Formulário de Linha (Composição)
class ItemComposicaoForm(forms.ModelForm):
    class Meta:
        model = ItemComposicao
        fields = ['material', 'quantidade_utilizada']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # AJUSTADO: Usando 'quantidade_estoque' em vez de 'quantidade'
        self.fields['material'].queryset = Material.objects.filter(quantidade_estoque__gt=0)
        
        # Sua estilização
        self.fields['material'].widget.attrs['class'] = 'form-select'
        self.fields['quantidade_utilizada'].widget.attrs['class'] = 'form-control'

# 4. O FormSet unindo tudo
ItemComposicaoFormSet = forms.inlineformset_factory(
    Produto, 
    ItemComposicao,
    form=ItemComposicaoForm,
    fields=['material', 'quantidade_utilizada'],
    extra=1,  # Número de formulários vazios para adicionar novos itens
    can_delete=True
)
# 5. Formulário de vendas
# atelier/forms.py

class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        # Atualize a lista de fields aqui:
        fields = ['valor_venda', 'metodo_pagamento', 'cliente', 'observacoes']
        
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}), # Agora é um dropdown de clientes
            'valor_venda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'metodo_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remova as linhas que tentavam estilizar 'nome_cliente' ou 'telefone_cliente'
        # Se quiser que todos os campos tenham a classe form-control automaticamente:
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
 
 # Entrada de material para o estoque       
class EntradaMaterialForm(forms.ModelForm):
    class Meta:
        model = EntradaMaterial
        fields = ['material', 'quantidade_adicionada', 'preco_unitario_na_compra']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantidade_adicionada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_unitario_na_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
#6. Form de categoria de material        
class CategoriaMaterialForm(forms.ModelForm):
    class Meta:
        model = CategoriaMaterial
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Tecidos, Linhas, Botões'}),
        }
        labels = {
            'nome': 'Nome da Categoria'
        }
        
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'email', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }