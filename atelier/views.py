from django.shortcuts import render, get_object_or_404, redirect
from atelier.models import Produto, Material, Venda, EntradaMaterial
from atelier.forms import ProdutoForm, ItemComposicaoFormSet, MaterialForm, VendaForm, EntradaMaterialForm
from django.db.models import Sum, F
from decimal import Decimal
from django.contrib import messages
from urllib.parse import quote


def index(request):
    # Filtramos apenas os materiais que estão abaixo ou igual ao estoque mínimo
    materiais_alerta = Material.objects.filter(quantidade_estoque__lte=models.F('estoque_minimo'))
    
    # Pegamos as últimas 5 vendas para um resumo rápido
    ultimas_vendas = Venda.objects.order_by('-data_venda')[:5]
    
    return render(request, 'atelier/lista_produtos.html', {
        'materiais_alerta': materiais_alerta,
        'ultimas_vendas': ultimas_vendas
    })


def registrar_entrada(request):
    material_id = request.GET.get('material') # Pega o ID da URL se existir
    
    if request.method == 'POST':
        form = EntradaMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_materiais')
    else:
        # Se veio um ID na URL, já deixa esse material selecionado no formulário
        initial_data = {'material': material_id} if material_id else {}
        form = EntradaMaterialForm(initial=initial_data) # O erro era o parêntese extra!
    
    return render(request, 'atelier/registrar_entrada.html', {'form': form})
   
def cadastrar_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_materiais') # Redireciona para a lista de materiais
    else:
        form = MaterialForm()
    
    return render(request, 'atelier/form_material.html', {'form': form})

def lista_materiais(request):
    materiais = Material.objects.all()
    return render(request, 'atelier/lista_materiais.html', {'materiais': materiais})


def editar_material(request, material_id):
    # Busca o material pelo ID ou retorna erro 404 se não existir
    material = get_object_or_404(Material, pk=material_id)
    
    if request.method == 'POST':
        # O segredo está no 'instance=material', que preenche o form com os dados atuais
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_materiais')
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'atelier/form_material.html', {'form': form, 'editando': True})

def excluir_material(request, material_id):
    material = get_object_or_404(Material, pk=material_id)
    
    if request.method == 'POST':
        material.delete()
        return redirect('atelier:lista_materiais')
    
    # Se não for POST (ou seja, se ela apenas clicou no link), 
    # mostramos uma página de confirmação.
    return render(request, 'atelier/confirmar_exclusao.html', {'item': material, 'tipo': 'material'})


def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        formset = ItemComposicaoFormSet(request.POST, request.FILES, instance=produto)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('atelier:detalhar_produto', produto_id=produto.id)
    else:
        form = ProdutoForm(instance=produto)
        formset = ItemComposicaoFormSet(instance=produto)
    
    return render(request, 'atelier/form_produto.html', {
        'form': form,
        'formset': formset,
        'editando': True
    })
    
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    
    if request.method == 'POST':
        produto.delete()
        return redirect('atelier:lista_produtos')
    
    return render(request, 'atelier/confirmar_exclusao_produto.html', {'item': produto, 'tipo': 'produto'})


def criar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)  # Inclui request.FILES para lidar com uploads de imagem
        formset = ItemComposicaoFormSet(request.POST, request.FILES,)
        
        if form.is_valid() and formset.is_valid():
            # Salva o produto primeiro
            produto = form.save()
            # Liga os materiais ao produto salvo e salva o formset
            instancias_materiais = formset.save(commit=False)
            for item in instancias_materiais:
                item.produto = produto
                item.save()
            return redirect('atelier:lista_produtos') # Redireciona após salvar
    else:
        form = ProdutoForm()
        formset = ItemComposicaoFormSet()
    
    return render(request, 'atelier/form_produto.html', {
        'form': form,
        'formset': formset
    })

def detalhar_produto(request, produto_id):
    # Busca o produto ou retorna 404
    produto = get_object_or_404(Produto, pk=produto_id)
    
    # Cálculos para exibir no detalhamento
    custo_materiais = produto.get_custo_total_materiais()
    custo_mao_de_obra = produto.tempo_trabalho_horas * produto.valor_hora_trabalho
    preco_final = produto.get_preco_final_sugerido()
    valor_lucro = preco_final - (custo_materiais + custo_mao_de_obra)
    custo_total_base = custo_materiais + custo_mao_de_obra

    context = {
        'produto': produto,
        'custo_materiais': custo_materiais,
        'custo_mao_de_obra': custo_mao_de_obra,
        'custo_total_base': custo_total_base,
        'preco_final': preco_final,
        'valor_lucro': valor_lucro,
    }
    
    return render(request, 'atelier/detalhe_produto.html', context)

def lista_produtos(request):
    # 1. Buscar todos os produtos (essencial para a sua tabela funcionar)
    produtos = Produto.objects.all().order_by('-id')
    
    # 2. Filtrar materiais para o alerta (quantidade <= estoque_minimo)
    materiais_alerta = Material.objects.filter(quantidade_estoque__lte=F('estoque_minimo'))
    
    # 3. Cálculos dos Cards (Investimento, Faturamento, Lucro)
    total_estoque_valor = sum(m.quantidade_estoque * m.preco_unitario for m in Material.objects.all())
    
    produtos_disponiveis = [p for p in produtos if not p.esta_vendido()]
    faturamento_potencial = sum(p.get_preco_final_sugerido() for p in produtos_disponiveis)
    lucro_estimado = sum(p.get_lucro_liquido() for p in produtos_disponiveis)

    # 4. Enviar TUDO para o template
    return render(request, 'atelier/lista_produtos.html', {
        'produtos': produtos, # <-- Faltava isso!
        'materiais_alerta': materiais_alerta,
        'total_estoque_valor': total_estoque_valor,
        'faturamento_potencial': faturamento_potencial,
        'lucro_estimado': lucro_estimado,
    })
    
def registrar_venda(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    
    if request.method == 'POST':
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)
            venda.produto = produto
            venda.save()
            
            # --- LÓGICA DO WHATSAPP AQUI ---
            link_whatsapp = ""
            if venda.telefone_cliente:
                # Montamos a mensagem exatamente como você quer
                mensagem = (
                    f"Olá {venda.nome_cliente}! "
                    f"Segue o recibo da sua compra: {venda.produto.nome}. "
                    f"Valor: R$ {venda.valor_venda:.2f}"
                )
                # O quote transforma espaços em %20 e acentos em códigos que o navegador entende
                mensagem_codificada = quote(mensagem)
                link_whatsapp = f"https://wa.me/55{venda.telefone_cliente}?text={mensagem_codificada}"
            # -------------------------------

            messages.success(request, f"Venda de {produto.nome} registrada!")
            
            # Passamos o 'venda' E o 'link_whatsapp' para o template
            return render(request, 'atelier/venda_confirmada.html', {
                'venda': venda, 
                'link_whatsapp': link_whatsapp
            })
            
    else:
        preco_sugerido = round(produto.get_preco_final_sugerido(), 2)
        form = VendaForm(initial={'valor_venda': preco_sugerido})

    return render(request, 'atelier/registrar_venda.html', {'form': form, 'produto': produto})

# A gerar_recibo continua igual, ela serve para imprimir/ver o PDF
def gerar_recibo(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)
    return render(request, 'atelier/recibo.html', {'venda': venda})


