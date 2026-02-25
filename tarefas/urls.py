from django.urls import path
from . import views

urlpatterns = [
    # Caminho vazio indica a página inicial do App
    path('', views.listar_tarefas, name='listar_tarefas'),
    # Rota para criar nova tarefa
    path('novo/', views.criar_tarefa, name='criar_tarefa'),
    # Rota que recebe um número inteiro (ID) para saber qual tarefa editar
    path('editar/<int:pk>/', views.editar_tarefa, name='editar_tarefa'),
    # Rota para excluir uma tarefa específica
    path('excluir/<int:pk>/', views.excluir_tarefa, name='excluir_tarefa'),
]