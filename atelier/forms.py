from django import forms
from .models import Produto, ItemComposicao, Material, Venda, EntradaMaterial

# 1. Formulário de Materiais (Estoque)
class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['nome', 'unidade_medida', 'preco_unitario', 'quantidade_estoque']
    widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
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
            'descricao': forms.Textarea(attrs={'rows': 2, 'style': 'resize:none;'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

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
class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ['metodo_pagamento', 'valor_venda', 'observacoes', 'nome_cliente', 'telefone_cliente']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 2}),
            'valor_venda': forms.NumberInput(attrs={'step': '0.01','class': 'form-control' }),
            'nome_cliente': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nome completo do cliente'
            }),
            'telefone_cliente': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '51999999999 (DDD + Número)'
            }),
            'metodo_pagamento': forms.Select(attrs={
                'class': 'form-select'
            }),                                       
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metodo_pagamento'].widget.attrs['class'] = 'form-select'
        self.fields['valor_venda'].widget.attrs['class'] = 'form-control'
        self.fields['observacoes'].widget.attrs['class'] = 'form-control'
        self.fields['nome_cliente'].widget.attrs['class'] = 'form-control'
        self.fields['telefone_cliente'].widget.attrs['class'] = 'form-control'
 
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