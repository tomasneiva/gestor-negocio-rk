from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente

from .extracao import processar_pdf
from .forms import NotaFiscalForm, NotaFiscalUploadForm
from .models import NotaFiscal, NotaFiscalItem


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


def editar(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    if request.method == "POST":
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota fiscal atualizada com sucesso.")
            return redirect("notas_fiscais:lista")
    else:
        form = NotaFiscalForm(instance=nota)
    return render(request, "notas_fiscais/editar.html", {"form": form, "nota": nota})


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
