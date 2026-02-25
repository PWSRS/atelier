import os
import django

# Configuração necessária para o script conversar com o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atelier.settings') # Ajuste 'seu_projeto' para o nome da sua pasta
django.setup()

from atelier.models import Material, Produto, ItemComposicao # Ajuste 'seu_app'

def popular():
    print("Iniciando a criação de dados de exemplo...")

    # 1. Criando Materiais (Estoque)
    tecido = Material.objects.get_or_create(nome="Linho", unidade_medida="Metro", preco_unitario=45.00)[0]
    botao = Material.objects.get_or_create(nome="Botão de Pérola", unidade_medida="Unidade", preco_unitario=2.50)[0]
    fita = Material.objects.get_or_create(nome="Fita de Cetim", unidade_medida="Metro", preco_unitario=5.00)[0]

    # 2. Criando um Produto
    # Vestido que leva 4 horas de trabalho, valor da hora R$ 50,00 e margem de 30%
    vestido = Produto.objects.get_or_create(
        nome="Vestido de Verão",
        descricao="Vestido leve com detalhes em pérola",
        tempo_trabalho_horas=4.0,
        valor_hora_trabalho=50.00,
        margem_lucro_percentual=30.0
    )[0]

    # 3. Adicionando a Composição (A "Receita" do Vestido)
    ItemComposicao.objects.get_or_create(produto=vestido, material=tecido, quantidade_utilizada=2.0) # 2 metros
    ItemComposicao.objects.get_or_create(produto=vestido, material=botao, quantidade_utilizada=10.0) # 10 botões
    ItemComposicao.objects.get_or_create(produto=vestido, material=fita, quantidade_utilizada=1.5)  # 1.5 metros

    print(f"Sucesso! Produto '{vestido.nome}' criado com os cálculos prontos.")

if __name__ == '__main__':
    popular()