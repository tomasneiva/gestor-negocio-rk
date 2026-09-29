from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PecaForm
from .models import Categoria, EstoqueItem, Peca, Unidade

SORT_MAP = {
    "preco": "peca__preco",
    "categoria": "peca__categoria__nome",
    "nome": "peca__nome",
}


def _unidade_id_atual(request):
    unidade_id = request.GET.get("unidade")
    if unidade_id:
        return unidade_id
    primeira = Unidade.objects.order_by("id").values_list("id", flat=True).first()
    return str(primeira) if primeira else ""


def _itens_filtrados(request, unidade_id):
    categoria_id = request.GET.get("categoria")
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "nome")

    itens = EstoqueItem.objects.select_related("peca", "peca__categoria", "unidade")
    if unidade_id:
        itens = itens.filter(unidade_id=unidade_id)
    if categoria_id:
        itens = itens.filter(peca__categoria_id=categoria_id)
    if q:
        itens = itens.filter(peca__nome__icontains=q)
    return itens.order_by(SORT_MAP.get(sort, "peca__nome"))


def _contexto_filtros(request, unidade_id):
    return {
        "unidades": Unidade.objects.order_by("id"),
        "categorias": Categoria.objects.order_by("nome"),
        "unidade_atual_id": unidade_id,
        "categoria_atual_id": request.GET.get("categoria", ""),
        "q": request.GET.get("q", ""),
        "sort": request.GET.get("sort", "nome"),
    }


def painel(request):
    unidade_id = _unidade_id_atual(request)
    contexto = _contexto_filtros(request, unidade_id)
    contexto["itens"] = _itens_filtrados(request, unidade_id)
    return render(request, "estoque/painel.html", contexto)


def tabela(request):
    unidade_id = _unidade_id_atual(request)
    itens = _itens_filtrados(request, unidade_id)
    return render(request, "estoque/_tabela.html", {"itens": itens})


def peca_lista(request):
    pecas = Peca.objects.select_related("categoria").order_by("nome")
    return render(request, "estoque/peca_lista.html", {"pecas": pecas})


def peca_criar(request):
    if request.method == "POST":
        form = PecaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Peça cadastrada com sucesso.")
            return redirect("estoque:peca_lista")
    else:
        form = PecaForm()
    return render(request, "estoque/peca_form.html", {"form": form, "titulo": "Nova peça"})


def peca_editar(request, pk):
    peca = get_object_or_404(Peca, pk=pk)
    if request.method == "POST":
        form = PecaForm(request.POST, request.FILES, instance=peca)
        if form.is_valid():
            form.save()
            messages.success(request, "Peça atualizada com sucesso.")
            return redirect("estoque:peca_lista")
    else:
        form = PecaForm(instance=peca)
    return render(request, "estoque/peca_form.html", {"form": form, "titulo": "Editar peça", "peca": peca})
