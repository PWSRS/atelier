from django.db import models

class Tarefa(models.Model):
    # Campo de texto para o título, limitado a 200 caracteres
    titulo = models.CharField(max_length=200)
    # Campo booleano (verdadeiro/falso) para o status da tarefa
    concluida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, blank=True, null=True) # Campo para o motivo da tarefa, pode ser deixado em branco

    # Define como o objeto aparece no painel administrativo (exibe o título em vez de "Object 1")
    def __str__(self):
        return f'{self.titulo} - {self.data_criacao.strftime("%Y-%m-%d %H:%M:%S")}'
