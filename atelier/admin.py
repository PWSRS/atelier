from django.contrib import admin
from .models import CategoriaMaterial, Material, EntradaMaterial, Produto, ItemComposicao, Venda, Cliente

# Inline para facilitar adicionar materiais na tela do Produto
class ItemComposicaoInline(admin.TabularInline):
    model = ItemComposicao
    extra = 1

# Inline para facilitar adicionar itens na tela da Venda (se necessário no futuro)
class ItemVendaInline(admin.TabularInline):                
    model = Venda
    extra = 1
    fk_name = 'cliente' # Define a relação correta

@admin.register(CategoriaMaterial)
class CategoriaMaterialAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'quantidade_estoque', 'unidade_medida', 'preco_unitario')
    search_fields = ('nome',)
    list_filter = ('categoria', 'unidade_medida')

@admin.register(EntradaMaterial)
class EntradaMaterialAdmin(admin.ModelAdmin):
    list_display = ('material', 'quantidade_adicionada', 'data_entrada')
    list_filter = ('material', 'data_entrada')

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tempo_trabalho_horas', 'margem_lucro_percentual', 'get_preco_final_sugerido')
    search_fields = ('nome',)
    inlines = [ItemComposicaoInline]
    
    # readonly_fields = ('preco_final',) # Opcional: torna o campo preco_final não editável manualmente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email', 'data_cadastro')
    search_fields = ('nome', 'telefone', 'email')
    ordering = ('-data_cadastro',)
    # inlines = [ItemVendaInline] # Opcional: mostra as vendas dentro do cliente no admin

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'produto', 'data_venda', 'valor_venda', 'metodo_pagamento')
    list_filter = ('metodo_pagamento', 'data_venda')
    search_fields = ('cliente__nome', 'produto__nome')
    date_hierarchy = 'data_venda'