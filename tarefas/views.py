from django.shortcuts import render, redirect, get_object_or_404
from .models import Tarefa
from .forms import TarefaForm

# VIEW DE LISTAGEM (Read)
def listar_tarefas(request):
    # Busca todas as tarefas salvas no banco de dados
    tarefas = Tarefa.objects.all()
    # Renderiza a página passando a lista de tarefas para o HTML
    return render(request, 'Tarefas/lista.html', {'tarefas': tarefas})

# VIEW DE CRIAÇÃO (Create)
def criar_tarefa(request):
    # Se o usuário enviou dados (POST), preenche o form com eles. Se não, abre vazio.
    form = TarefaForm(request.POST or None)
    # Verifica se os dados enviados são válidos
    if form.is_valid():
        form.save() # Salva no banco de dados
        return redirect('listar_tarefas') # Volta para a lista principal
    return render(request, 'Tarefas/form.html', {'form': form})

# VIEW DE EDIÇÃO (Update)
def editar_tarefa(request, pk):
    # Busca a tarefa pelo ID (pk) ou retorna erro 404 se não existir
    tarefa = get_object_or_404(Tarefa, pk=pk)
    # Preenche o formulário com os dados da tarefa existente
    form = TarefaForm(request.POST or None, instance=tarefa)
    if form.is_valid():
        form.save()
        return redirect('listar_tarefas')
    return render(request, 'Tarefas/form.html', {'form': form})

# VIEW DE EXCLUSÃO (Delete)
def excluir_tarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    # Só deleta se o usuário confirmar via método POST (segurança)
    if request.method == 'POST':
        tarefa.delete()
        return redirect('listar_tarefas')
    return render(request, 'Tarefas/confirmar_exclusao.html', {'tarefa': tarefa})