from django import forms
from .models import Tarefa

class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['titulo', 'concluida', 'motivo']
        
        # Aqui personalizamos a aparência dos campos
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Digite o nome da tarefa...'
            }),
            'concluida': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Digite o motivo da tarefa...'
            }),
        }
        
        # Também podemos traduzir as labels (rótulos) aqui
        labels = {
            'titulo': 'Título da Tarefa',
            'concluida': 'Já está concluída?',
        }