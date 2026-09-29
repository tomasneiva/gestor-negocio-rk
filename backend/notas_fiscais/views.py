import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente
from estoque.forms import PecaForm
from estoque.models import Peca

from .extracao import processar_pdf
from .forms import NotaFiscalForm, NotaFiscalUploadForm
from .models import NotaFiscal, NotaFiscalItem

logger = logging.getLogger(__name__)


def _itens_sem_peca_cadastrada(nota):
    nomes_cadastrados = {nome.strip().lower() for nome in Peca.objects.values_list("nome", flat=True)}
    vistos = set()
    pendentes = []
    for item in nota.itens.all():
        nome_normalizado = (item.descricao or "").strip().lower()
        if not nome_normalizado or nome_normalizado in nomes_cadastrados or nome_normalizado in vistos:
            continue
        vistos.add(nome_normalizado)
        pendentes.append(item)
    return pendentes


def lista(request):
    notas = NotaFiscal.objects.select_related("cliente").all()
    return render(request, "notas_fiscais/lista.html", {"notas": notas})


def enviar(request):
    if request.method == "POST":
        form = NotaFiscalUploadForm(request.POST, request.FILES)
        if form.is_valid():
            nota = form.save()
            _processar_e_preencher(nota)
            messages.success(request, "NF enviada e processada. Confira os dados extraídos abaixo.")
            return redirect("notas_fiscais:editar", pk=nota.pk)
    else:
        form = NotaFiscalUploadForm()
    return render(request, "notas_fiscais/enviar.html", {"form": form})


def enviar_lote(request):
    if request.method == "POST":
        arquivos = request.FILES.getlist("arquivos")
        if not arquivos:
            messages.error(request, "Selecione ao menos um arquivo PDF.")
            return render(request, "notas_fiscais/enviar_lote.html")

        resultados = []
        for arquivo in arquivos:
            form = NotaFiscalUploadForm(files={"arquivo": arquivo})
            if not form.is_valid():
                erro = "; ".join(form.errors.get("arquivo", ["Arquivo inválido."]))
                resultados.append({"nome": arquivo.name, "ok": False, "erro": erro})
                continue
            try:
                nota = form.save()
                _processar_e_preencher(nota)
                resultados.append({"nome": arquivo.name, "ok": True, "nota": nota})
            except Exception:
                logger.exception("Falha ao processar NF em lote: %s", arquivo.name)
                resultados.append({"nome": arquivo.name, "ok": False, "erro": "Falha ao processar o PDF."})

        return render(request, "notas_fiscais/enviar_lote_resultado.html", {"resultados": resultados})
    return render(request, "notas_fiscais/enviar_lote.html")


def editar(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    if request.method == "POST":
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota fiscal atualizada com sucesso.")
            if _itens_sem_peca_cadastrada(nota):
                return redirect("notas_fiscais:produtos_pendentes", pk=nota.pk)
            return redirect("notas_fiscais:lista")
    else:
        form = NotaFiscalForm(instance=nota)
    itens_pendentes = _itens_sem_peca_cadastrada(nota)
    return render(request, "notas_fiscais/editar.html", {
        "form": form, "nota": nota, "itens_pendentes": itens_pendentes,
    })


def produtos_pendentes(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    itens_pendentes = _itens_sem_peca_cadastrada(nota)
    if not itens_pendentes:
        messages.info(request, "Todos os produtos desta nota já estão cadastrados no estoque.")
        return redirect("notas_fiscais:lista")

    PecaFormSet = modelformset_factory(Peca, form=PecaForm, extra=len(itens_pendentes))

    initial = []
    for item in itens_pendentes:
        dados = {"nome": item.descricao, "codigo": item.codigo}
        if item.valor_unitario:
            dados["preco"] = item.valor_unitario
        initial.append(dados)

    if request.method == "POST":
        formset = PecaFormSet(request.POST, request.FILES, queryset=Peca.objects.none(), initial=initial)
        if formset.is_valid():
            criadas = formset.save()
            if criadas:
                messages.success(request, f"{len(criadas)} produto(s) cadastrado(s) com sucesso.")
            return redirect("notas_fiscais:produtos_pendentes", pk=nota.pk)
    else:
        formset = PecaFormSet(queryset=Peca.objects.none(), initial=initial)

    return render(request, "notas_fiscais/produtos_pendentes.html", {
        "nota": nota, "formset": formset,
    })


def _processar_e_preencher(nota):
    with nota.arquivo.open("rb") as arquivo:
        extraido = processar_pdf(arquivo)

    nota.chave_acesso = extraido.chave_acesso
    nota.numero = extraido.numero
    nota.serie = extraido.serie
    nota.natureza_operacao = extraido.natureza_operacao
    nota.observacoes = extraido.observacoes
    nota.texto_extraido = extraido.texto_bruto
    if extraido.data_emissao:
        nota.data_emissao = extraido.data_emissao
    if extraido.valor_produtos:
        nota.valor_produtos = extraido.valor_produtos
    if extraido.desconto:
        nota.desconto = extraido.desconto
    if extraido.valor_total:
        nota.valor_total = extraido.valor_total

    if extraido.cliente.documento:
        cliente = Cliente.objects.filter(documento=extraido.cliente.documento).first()
        if not cliente and extraido.cliente.nome and extraido.cliente.cep:
            tipo = (
                Cliente.TipoPessoa.JURIDICA
                if len(extraido.cliente.documento) == 14
                else Cliente.TipoPessoa.FISICA
            )
            novo_cliente = Cliente(
                tipo_pessoa=tipo,
                nome=extraido.cliente.nome,
                documento=extraido.cliente.documento,
                cep=extraido.cliente.cep,
                cidade=extraido.cliente.municipio,
                uf=extraido.cliente.uf,
            )
            try:
                novo_cliente.full_clean()
                novo_cliente.save()
                cliente = novo_cliente
            except ValidationError:
                cliente = None
        if cliente:
            nota.cliente = cliente

    nota.save()

    for item in extraido.itens:
        NotaFiscalItem.objects.create(
            nota_fiscal=nota,
            codigo=item.codigo,
            descricao=item.descricao,
            ncm=item.ncm,
            cfop=item.cfop,
            unidade=item.unidade,
            quantidade=item.quantidade or None,
            valor_unitario=item.valor_unitario or None,
            valor_total=item.valor_total or None,
        )
