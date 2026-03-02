from django.urls import path
from . import views

app_name = 'atelier' # Isso é fundamental!

urlpatterns = [
    path('', views.lista_produtos, name='lista_produtos'),
    path('produto/novo/', views.criar_produto, name='criar_produto'),
    path('produto/editar/<int:produto_id>/', views.editar_produto, name='editar_produto'),
    path('produto/<int:produto_id>/', views.detalhar_produto, name='detalhar_produto'),
    path('produto/excluir/<int:produto_id>/', views.excluir_produto, name='excluir_produto'),
    path('materiais/', views.lista_materiais, name='lista_materiais'),
    path('materiais/novo/', views.cadastrar_material, name='cadastrar_material'),
    path('material/novo-modal/', views.cadastrar_material_modal, name='cadastrar_material_modal'),
    path('materiais/categoria/nova/', views.cadastrar_categoria, name='cadastrar_categoria'),
    path('materiais/editar/<int:material_id>/', views.editar_material, name='editar_material'),
    path('materiais/excluir/<int:material_id>/', views.excluir_material, name='excluir_material'),
    path('vender/<int:produto_id>/', views.registrar_venda, name='registrar_venda'),
    path('venda/recibo/<int:venda_id>/', views.gerar_recibo, name='gerar_recibo'),
    path('material/entrada/', views.registrar_entrada, name='registrar_entrada'),
    # URLs de Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('clientes/<int:cliente_id>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/excluir/', views.excluir_cliente, name='excluir_cliente'),
]