from django.shortcuts import render, get_object_or_404, redirect
from atelier.models import Produto, Material, Venda, EntradaMaterial, CategoriaMaterial, Cliente
from atelier.forms import ProdutoForm, ItemComposicaoFormSet, MaterialForm, VendaForm, EntradaMaterialForm, CategoriaMaterialForm, ClienteForm
from django.db.models import Sum, F
from decimal import Decimal
from django.contrib import messages
from urllib.parse import quote
from django.http import JsonResponse
from django.utils import timezone
import datetime


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
   

def cadastrar_categoria(request):
    if request.method == 'POST':
        form = CategoriaMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_materiais') # Volta para a lista de materiais
    else:
        form = CategoriaMaterialForm()
    
    return render(request, 'atelier/cadastrar_categoria.html', {'form': form})

def cadastrar_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_materiais') # Redireciona para a lista de materiais
    else:
        form = MaterialForm()
    
    return render(request, 'atelier/form_material.html', {'form': form})

def cadastrar_material_modal(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            # Retorna sucesso e os dados básicos do novo material
            return JsonResponse({
                'success': True,
                'nome': material.nome,
                'categoria_id': material.categoria.id if material.categoria else None,
                'unidade': material.get_unidade_medida_display(),
                'preco': float(material.preco_unitario),
                'quantidade': float(material.quantidade_estoque),
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False}, status=400)

def lista_materiais(request):
    # Busca categorias e os materiais dentro de cada uma (eficiente para o banco de dados)
    categorias = CategoriaMaterial.objects.prefetch_related('materiais').all()
    
    # Busca materiais que ainda não foram vinculados a nenhuma categoria
    materiais_sem_categoria = Material.objects.filter(categoria__isnull=True)
    
    form_modal = MaterialForm()
    
    return render(request, 'atelier/lista_materiais.html', {
        'categorias': categorias,
        'materiais_sem_categoria': materiais_sem_categoria,
        'form_modal': form_modal,
    })

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
        formset = ItemComposicaoFormSet(request.POST, instance=produto) # Vincula ao produto
        
        if form.is_valid() and formset.is_valid():
            # Salva o produto e aplica a lógica do tempo (mesma da criação)
            produto = form.save(commit=False)
            
            # (Opcional) Re-garantir a conversão se necessário, 
            # mas se o form.py estiver com TimeInput, o Django cuida disso.
            
            produto.save()
            formset.save()
            
            # Recalcula o preço após salvar os itens do formset
            produto.calcular_e_salvar_preco()
            
            return redirect('atelier:lista_produtos')
    else:
        # No GET, carregamos o produto e seus materiais existentes
        form = ProdutoForm(instance=produto)
        formset = ItemComposicaoFormSet(instance=produto)
    
    return render(request, 'atelier/form_produto.html', {
        'form': form,
        'formset': formset,
        'produto': produto # Útil para o título da página "Editando..."
    })
    
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    
    if request.method == 'POST':
        produto.delete()
        return redirect('atelier:lista_produtos')
    
    return render(request, 'atelier/confirmar_exclusao_produto.html', {'item': produto, 'tipo': 'produto'})


def criar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)
        formset = ItemComposicaoFormSet(request.POST) 
        
        if form.is_valid() and formset.is_valid():
            # Salva o produto (o Django converte a string HH:MM para objeto time automaticamente)
            produto = form.save(commit=False)
            
            # --- NÃO PRECISA MAIS DE CONVERSÃO MANUAL AQUI ---
            # O get_tempo_em_decimal() do modelo cuidará disso na hora do cálculo
            
            produto.save()
            
            # Vincula o formset e salva
            formset.instance = produto
            formset.save()
            
            # --- CALCULA O PREÇO FINAL ---
            # Chama o método do modelo para calcular baseado no TimeField
            produto.calcular_e_salvar_preco()
            
            return redirect('atelier:lista_produtos')
    else:
        form = ProdutoForm()
        formset = ItemComposicaoFormSet(instance=Produto()) 
    
    return render(request, 'atelier/form_produto.html', {
        'form': form,
        'formset': formset
    })  
    
def detalhar_produto(request, produto_id):
    # Busca o produto ou retorna 404
    produto = get_object_or_404(Produto, pk=produto_id)
    
    # --- CORREÇÃO AQUI ---
    # Busca o custo dos materiais (retorna Decimal)
    custo_materiais = produto.get_custo_total_materiais()
    
    # Converte o tempo para Decimal antes de multiplicar (retorna Decimal)
    tempo_decimal = produto.get_tempo_em_decimal()
    custo_mao_de_obra = tempo_decimal * produto.valor_hora_trabalho
    
    # Cálculos usando os valores já corrigidos
    preco_final = produto.get_preco_final_sugerido()
    valor_lucro = preco_final - (custo_materiais + custo_mao_de_obra)
    custo_total_base = custo_materiais + custo_mao_de_obra
    # ---------------------

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
    
    # --- NOVO CÁLCULO FINANCEIRO REAL ---
    # 1. Total faturado (soma de todas as vendas)
    total_faturado_real = Venda.objects.aggregate(total=Sum('valor_venda'))['total'] or 0
    
    # 2. Lucro Real Acumulado
    # Buscamos produtos que têm venda associada
    produtos_vendidos = Produto.objects.filter(vendas__isnull=False).distinct()
    lucro_real_acumulado = sum(p.get_lucro_liquido() for p in produtos_vendidos)
    # -------------------------------------

    # 4. Enviar TUDO para o template
    return render(request, 'atelier/lista_produtos.html', {
        'produtos': produtos,
        'materiais_alerta': materiais_alerta,
        'total_estoque_valor': total_estoque_valor,
        'faturamento_potencial': faturamento_potencial,
        'lucro_estimado': lucro_estimado,
        'total_faturado_real': total_faturado_real,
        'lucro_real_acumulado': lucro_real_acumulado,
    })
    
def registrar_venda(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    
    if request.method == 'POST':
        form = VendaForm(request.POST)
        if form.is_valid():
            
            venda = form.save(commit=False)
            
            # 1. Definimos o produto que veio da URL
            venda.produto = produto
            
            # 2. Definimos a data e hora atual automaticamente
            venda.data_venda = timezone.now()
            
            venda.save()
            # ---------------------
            
            # ... Lógica do WhatsApp (igual antes) ...
            link_whatsapp = ""
            if venda.cliente:
                mensagem = (
                    f"Olá {venda.cliente.nome}! "
                    f"Segue o recibo da sua compra: {venda.produto.nome}. "
                    f"Valor: R$ {venda.valor_venda:.2f}"
                )
                link_whatsapp = f"https://wa.me/55{venda.cliente.telefone}?text={quote(mensagem)}"

            messages.success(request, f"Venda de {produto.nome} registrada!")
            return render(request, 'atelier/venda_confirmada.html', {
                'venda': venda, 
                'link_whatsapp': link_whatsapp
            })
        else:
            # DICA: Ver o erro no terminal
            print("❌ FORMULÁRIO INVÁLIDO")
            print(form.errors) 
            
    else:
        preco_sugerido = round(produto.get_preco_final_sugerido(), 2)
        form = VendaForm(initial={'valor_venda': preco_sugerido})

    return render(request, 'atelier/registrar_venda.html', {'form': form, 'produto': produto})

# A gerar_recibo continua igual, ela serve para imprimir/ver o PDF
def gerar_recibo(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id)
    return render(request, 'atelier/recibo.html', {'venda': venda})


# LISTAGEM GERAL
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('nome')
    return render(request, 'atelier/lista_clientes.html', {'clientes': clientes})

# CADASTRO
def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'atelier/form_cliente.html', {'form': form, 'editando': False})

# EDIÇÃO
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('atelier:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'atelier/form_cliente.html', {'form': form, 'editando': True})

# EXCLUSÃO
def excluir_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        cliente.delete()
        return redirect('atelier:lista_clientes')
    return render(request, 'atelier/confirmar_exclusao.html', {'item': cliente, 'tipo': 'cliente'})

# DETALHES E HISTÓRICO DE COMPRAS (A parte "Prudente")
def detalhe_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    # Buscamos as vendas vinculadas a este cliente específico
    compras = cliente.vendas.all().order_by('-data_venda')
    total_compras = compras.aggregate(Sum('valor_venda'))['valor_venda__sum'] or 0
    return render(request, 'atelier/detalhe_cliente.html', {
        'cliente': cliente,
        'compras': compras,
        'total_compras': total_compras
    })



