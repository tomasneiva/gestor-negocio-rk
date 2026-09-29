# TEMP-DEBUG: prints marcados com [DEBUG-PEDIDOS] em todo o arquivo -- remover quando o diagnostico terminar
import traceback

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from estoque.models import Peca

from .forms import PedidoVendaForm, PedidoVendaItemFormSet
from .models import PedidoVenda
from .pdf import gerar_pdf_pedido


def _log(msg):
    print(f"[DEBUG-PEDIDOS] {msg}", flush=True)


def _precos_pecas():
    _log("_precos_pecas: consultando precos de pecas")
    precos = dict(Peca.objects.values_list("pk", "preco"))
    _log(f"_precos_pecas: {len(precos)} pecas encontradas")
    return precos


def lista(request):
    _log("lista: inicio")
    pedidos = PedidoVenda.objects.select_related("cliente", "unidade")
    status = request.GET.get("status", "")
    if status:
        pedidos = pedidos.filter(status=status)
    _log(f"lista: renderizando, status_filtro={status!r}")
    resp = render(request, "pedidos/lista.html", {
        "pedidos": pedidos,
        "status_atual": status,
        "status_choices": PedidoVenda.Status.choices,
    })
    _log("lista: fim")
    return resp


def criar(request):
    _log(f"criar: inicio, method={request.method}")
    try:
        if request.method == "POST":
            _log(f"criar: POST recebido, keys={list(request.POST.keys())}")
            form = PedidoVendaForm(request.POST)
            _log("criar: PedidoVendaForm construido")
            formset = PedidoVendaItemFormSet(request.POST, form_kwargs={"precos": _precos_pecas()})
            _log("criar: formset construido")
            form_valido = form.is_valid()
            _log(f"criar: form.is_valid()={form_valido} errors={form.errors.as_json() if not form_valido else '{}'}")
            formset_valido = formset.is_valid()
            _log(
                f"criar: formset.is_valid()={formset_valido} "
                f"non_form_errors={formset.non_form_errors()} "
                f"errors={[f.errors for f in formset.forms]}"
            )
            if form_valido and formset_valido:
                _log("criar: salvando form (pedido)")
                pedido = form.save()
                _log(f"criar: pedido salvo pk={pedido.pk}")
                formset.instance = pedido
                _log("criar: salvando formset (itens)")
                formset.save()
                _log("criar: formset salvo com sucesso")
                messages.success(request, "Pedido criado em rascunho.")
                _log(f"criar: redirecionando para detalhe pk={pedido.pk}")
                return redirect("pedidos:detalhe", pk=pedido.pk)
        else:
            _log("criar: GET, montando form/formset vazios")
            form = PedidoVendaForm()
            formset = PedidoVendaItemFormSet(form_kwargs={"precos": _precos_pecas()})
        _log("criar: renderizando template form.html")
        resp = render(request, "pedidos/form.html", {
            "form": form, "formset": formset, "titulo": "Novo pedido de venda",
        })
        _log("criar: fim (render concluido)")
        return resp
    except Exception:
        _log("criar: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise


def editar(request, pk):
    _log(f"editar: inicio pk={pk} method={request.method}")
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    if not pedido.pode_editar:
        _log(f"editar: pedido {pk} nao esta em rascunho, redirecionando")
        messages.error(request, "Só é possível editar pedidos em rascunho.")
        return redirect("pedidos:detalhe", pk=pedido.pk)
    try:
        if request.method == "POST":
            form = PedidoVendaForm(request.POST, instance=pedido)
            formset = PedidoVendaItemFormSet(request.POST, instance=pedido, form_kwargs={"precos": _precos_pecas()})
            form_valido = form.is_valid()
            formset_valido = formset.is_valid()
            _log(f"editar: form.is_valid()={form_valido} formset.is_valid()={formset_valido}")
            if form_valido and formset_valido:
                form.save()
                formset.save()
                _log(f"editar: pedido {pk} salvo com sucesso")
                messages.success(request, "Pedido atualizado.")
                return redirect("pedidos:detalhe", pk=pedido.pk)
        else:
            form = PedidoVendaForm(instance=pedido)
            formset = PedidoVendaItemFormSet(instance=pedido, form_kwargs={"precos": _precos_pecas()})
        _log(f"editar: renderizando template form.html pk={pk}")
        return render(request, "pedidos/form.html", {
            "form": form, "formset": formset, "titulo": f"Editar pedido #{pedido.pk}", "pedido": pedido,
        })
    except Exception:
        _log("editar: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise


def detalhe(request, pk):
    _log(f"detalhe: inicio pk={pk}")
    pedido = get_object_or_404(
        PedidoVenda.objects.select_related("cliente", "unidade"), pk=pk
    )
    resp = render(request, "pedidos/detalhe.html", {"pedido": pedido})
    _log(f"detalhe: fim pk={pk}")
    return resp


@require_POST
def confirmar(request, pk):
    _log(f"confirmar: inicio pk={pk}")
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        pedido.confirmar()
        _log(f"confirmar: pedido {pk} confirmado")
        messages.success(request, "Pedido confirmado.")
    except ValidationError as e:
        _log(f"confirmar: ValidationError {e.messages}")
        messages.error(request, " ".join(e.messages))
    except Exception:
        _log("confirmar: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise
    return redirect("pedidos:detalhe", pk=pedido.pk)


@require_POST
def cancelar(request, pk):
    _log(f"cancelar: inicio pk={pk}")
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        pedido.cancelar()
        _log(f"cancelar: pedido {pk} cancelado")
        messages.success(request, "Pedido cancelado.")
    except ValidationError as e:
        _log(f"cancelar: ValidationError {e.messages}")
        messages.error(request, " ".join(e.messages))
    except Exception:
        _log("cancelar: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise
    return redirect("pedidos:detalhe", pk=pedido.pk)


@require_POST
def baixar_estoque(request, pk):
    _log(f"baixar_estoque: inicio pk={pk}")
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        avisos = pedido.dar_baixa_estoque()
        _log(f"baixar_estoque: pedido {pk} baixado, avisos={avisos}")
        messages.success(request, "Baixa de estoque lançada.")
        for aviso in avisos:
            messages.warning(request, aviso)
    except ValidationError as e:
        _log(f"baixar_estoque: ValidationError {e.messages}")
        messages.error(request, " ".join(e.messages))
    except Exception:
        _log("baixar_estoque: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise
    return redirect("pedidos:detalhe", pk=pedido.pk)


@require_POST
def desfazer_baixa(request, pk):
    _log(f"desfazer_baixa: inicio pk={pk}")
    pedido = get_object_or_404(PedidoVenda, pk=pk)
    try:
        pedido.desfazer_baixa_estoque()
        _log(f"desfazer_baixa: pedido {pk} baixa desfeita")
        messages.success(request, "Baixa de estoque desfeita.")
    except Exception:
        _log("desfazer_baixa: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise
    return redirect("pedidos:detalhe", pk=pedido.pk)


def pdf(request, pk):
    _log(f"pdf: inicio pk={pk}")
    try:
        pedido = get_object_or_404(
            PedidoVenda.objects.select_related("cliente", "unidade"), pk=pk
        )
        buffer = gerar_pdf_pedido(pedido)
        _log(f"pdf: gerado com sucesso pk={pk}")
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="pedido-{pedido.pk}.pdf"'
        return response
    except Exception:
        _log("pdf: EXCECAO NAO TRATADA:\n" + traceback.format_exc())
        raise
