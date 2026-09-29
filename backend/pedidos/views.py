from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from estoque.models import Peca

from .forms import PedidoVendaForm, PedidoVendaItemFormSet
from .models import PedidoVenda
from .pdf import gerar_pdf_pedido


def _precos_pecas():
    return dict(Peca.objects.values_list("pk", "preco"))


def lista(request):
    pedidos = PedidoVenda.objects.select_related("cliente", "unidade")
    status = request.GET.get("status", "")
    if status:
        pedidos = pedidos.filter(status=status)
    return render(request, "pedidos/lista.html", {
        "pedidos": pedidos,
        "status_atual": status,
        "status_choices": PedidoVenda.Status.choices,
    })


def criar(request):
    if request.method == "POST":
        form = PedidoVendaForm(request.POST)
        formset = PedidoVendaItemFormSet(request.POST, form_kwargs={"precos": _precos_pecas()})
        if form.is_valid() and formset.is_valid():
            pedido = form.save()
            formset.instance = pedido
            formset.save()
            messages.success(request, "Pedido criado em rascunho.")
            return redirect("pedidos:detalhe", pk=pedido.pk)
    else:
        form = PedidoVendaForm()
        formset = PedidoVendaItemFormSet(form_kwargs={"precos": _precos_pecas()})
    return render(request, "pedidos/form.html", {
        "form": form, "formset": formset, "titulo": "Novo pedido de venda",
    })


def editar(request, pk):
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    if not pedido.pode_editar:
        messages.error(request, "Só é possível editar pedidos em rascunho.")
        return redirect("pedidos:detalhe", pk=pedido.pk)
    if request.method == "POST":
        form = PedidoVendaForm(request.POST, instance=pedido)
        formset = PedidoVendaItemFormSet(request.POST, instance=pedido, form_kwargs={"precos": _precos_pecas()})
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Pedido atualizado.")
            return redirect("pedidos:detalhe", pk=pedido.pk)
    else:
        form = PedidoVendaForm(instance=pedido)
        formset = PedidoVendaItemFormSet(instance=pedido, form_kwargs={"precos": _precos_pecas()})
    return render(request, "pedidos/form.html", {
        "form": form, "formset": formset, "titulo": f"Editar pedido #{pedido.pk}", "pedido": pedido,
    })


def detalhe(request, pk):
    pedido = get_object_or_404(
        PedidoVenda.objects.select_related("cliente", "unidade"), pk=pk
    )
    return render(request, "pedidos/detalhe.html", {"pedido": pedido})


@require_POST
def confirmar(request, pk):
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        pedido.confirmar()
        messages.success(request, "Pedido confirmado.")
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
    return redirect("pedidos:detalhe", pk=pedido.pk)


@require_POST
def cancelar(request, pk):
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        pedido.cancelar()
        messages.success(request, "Pedido cancelado.")
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
    return redirect("pedidos:detalhe", pk=pedido.pk)


@require_POST
def baixar_estoque(request, pk):
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        avisos = pedido.dar_baixa_estoque()
        messages.success(request, "Baixa de estoque lançada.")
        for aviso in avisos:
            messages.warning(request, aviso)
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
    return redirect("pedidos:detalhe", pk=pedido.pk)


@require_POST
def desfazer_baixa(request, pk):
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    pedido.desfazer_baixa_estoque()
    messages.success(request, "Baixa de estoque desfeita.")
    return redirect("pedidos:detalhe", pk=pedido.pk)


def pdf(request, pk):
    pedido = get_object_or_404(
        PedidoVenda.objects.select_related("cliente", "unidade"), pk=pk
    )
    buffer = gerar_pdf_pedido(pedido)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="pedido-{pedido.pk}.pdf"'
    return response
