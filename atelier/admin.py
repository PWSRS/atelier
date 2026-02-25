from django.contrib import admin
from .models import Material, Produto, ItemComposicao

# Isso permite adicionar materiais direto na tela do Produto (como fizemos no formset)
class ItemComposicaoInline(admin.TabularInline):
    model = ItemComposicao
    extra = 1

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'unidade_medida', 'preco_unitario')
    search_fields = ('nome',)
    list_filter = ('unidade_medida',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    # Exibe colunas importantes na listagem
    list_display = ('nome', 'tempo_trabalho_horas', 'valor_hora_trabalho', 'get_preco_venda')
    search_fields = ('nome',)
    
    # Adiciona a lista de materiais dentro da edição do produto
    inlines = [ItemComposicaoInline]

    # Criamos um método para mostrar o preço calculado no Admin
    def get_preco_venda(self, obj):
        return f"R$ {obj.get_preco_final_sugerido():.2f}"
    
    get_preco_venda.short_description = 'Preço Sugerido'