import re
from dataclasses import dataclass, field

UFS_VALIDAS = (
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO"
).split()

PADRAO_DOCUMENTO = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2}")
PADRAO_CHAVE_ACESSO = re.compile(r"(?:\d{4}\s){10}\d{4}")
PADRAO_UF = re.compile(r"\b(" + "|".join(UFS_VALIDAS) + r")\b")


@dataclass
class ClienteExtraido:
    nome: str = ""
    documento: str = ""
    cep: str = ""
    municipio: str = ""
    uf: str = ""


@dataclass
class ItemExtraido:
    codigo: str = ""
    descricao: str = ""
    ncm: str = ""
    cfop: str = ""
    unidade: str = ""
    quantidade: str = ""
    valor_unitario: str = ""
    valor_total: str = ""


@dataclass
class NotaFiscalExtraida:
    chave_acesso: str = ""
    numero: str = ""
    serie: str = ""
    natureza_operacao: str = ""
    data_emissao: str = ""
    valor_produtos: str = ""
    desconto: str = ""
    valor_total: str = ""
    observacoes: str = ""
    cliente: ClienteExtraido = field(default_factory=ClienteExtraido)
    itens: list = field(default_factory=list)
    texto_bruto: str = ""


def extrair_texto(arquivo) -> str:
    import pdfplumber

    with pdfplumber.open(arquivo) as pdf:
        return "\n".join((pagina.extract_text() or "") for pagina in pdf.pages)


def _buscar(padrao, texto, grupo=1, flags=re.IGNORECASE):
    m = re.search(padrao, texto, flags)
    return m.group(grupo).strip() if m else ""


def _para_decimal(valor_str):
    if not valor_str:
        return ""
    return valor_str.strip().replace(".", "").replace(",", ".")


def _para_data_iso(data_br):
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", data_br or "")
    if not m:
        return ""
    dia, mes, ano = m.groups()
    return f"{ano}-{mes}-{dia}"


def _extrair_bloco_destinatario(texto):
    return _buscar(
        r"Destinat[áa]rio/?Remetente\s*\n(.*?)(?:\nFaturas)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _extrair_cliente(bloco):
    cliente = ClienteExtraido()
    if not bloco:
        return cliente

    doc_m = PADRAO_DOCUMENTO.search(bloco)
    if doc_m:
        cliente.documento = re.sub(r"\D", "", doc_m.group(0))
        for linha in bloco.splitlines():
            if doc_m.group(0) in linha:
                cliente.nome = linha.split(doc_m.group(0))[0].strip()
                break

    cep_m = re.search(r"\d{2}\.?\d{3}-\d{3}", bloco)
    if cep_m:
        cliente.cep = re.sub(r"\D", "", cep_m.group(0))

    uf_m = PADRAO_UF.search(bloco)
    if uf_m:
        cliente.uf = uf_m.group(1)
        for linha in bloco.splitlines():
            if uf_m.group(1) in linha:
                cliente.municipio = linha.split(uf_m.group(1))[0].strip()
                break

    return cliente


def _extrair_totais(texto):
    """A caixa 'Cálculo do imposto' tem ordem de campos padronizada pela SEFAZ:
    a linha de rótulos e a linha de valores seguem a mesma sequência posicional."""
    linhas = texto.splitlines()
    produtos = desconto = total = ""

    idx1 = next(
        (i for i, l in enumerate(linhas) if "Base de c" in l and "ICMS" in l and i + 1 < len(linhas)),
        None,
    )
    if idx1 is not None:
        valores = re.findall(r"[\d.,]+", linhas[idx1 + 1])
        if valores:
            produtos = _para_decimal(valores[-1])

    idx2 = next(
        (i for i, l in enumerate(linhas) if l.strip().startswith("Valor do frete") and i + 1 < len(linhas)),
        None,
    )
    if idx2 is not None:
        valores = re.findall(r"[\d.,]+", linhas[idx2 + 1])
        if len(valores) >= 6:
            desconto = _para_decimal(valores[2])
            total = _para_decimal(valores[-1])

    return produtos, desconto, total


def processar_pdf(arquivo) -> NotaFiscalExtraida:
    texto = extrair_texto(arquivo)
    nf = NotaFiscalExtraida(texto_bruto=texto)

    chave_m = PADRAO_CHAVE_ACESSO.search(texto)
    if chave_m:
        nf.chave_acesso = re.sub(r"\D", "", chave_m.group(0))

    nf.numero = _buscar(r"N[ºo°]\s*(\d{1,9})", texto)
    nf.serie = _buscar(r"S[ée]rie[:\s]+(\d+)", texto)

    natureza_valor = _buscar(r"Natureza da opera[cç][aã]o[^\n]*\n(.+)", texto)
    nf.natureza_operacao = re.split(r"\s+\d{8,}", natureza_valor)[0].strip()

    bloco_dest = _extrair_bloco_destinatario(texto)
    nf.cliente = _extrair_cliente(bloco_dest)

    data_m = re.search(r"\d{2}/\d{2}/\d{4}", bloco_dest) if bloco_dest else None
    if data_m:
        nf.data_emissao = _para_data_iso(data_m.group(0))

    nf.valor_produtos, nf.desconto, nf.valor_total = _extrair_totais(texto)

    nf.observacoes = _buscar(
        r"Observa[cç][oõ]es[^\n]*\n(.+?)(?:\n\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    padrao_item = re.compile(
        r"^(\S+)\s+(.+?)\s+(\d{8})\s+(\d{4})\s+(\d\.\d{3})\s+(\w+)\s+"
        r"([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s*$",
        re.MULTILINE,
    )
    for m in padrao_item.finditer(texto):
        codigo, descricao, ncm, _csosn, cfop, un, qtde, preco_un, preco_total, *_ = m.groups()
        nf.itens.append(
            ItemExtraido(
                codigo=codigo,
                descricao=descricao.strip(),
                ncm=ncm,
                cfop=cfop,
                unidade=un,
                quantidade=_para_decimal(qtde),
                valor_unitario=_para_decimal(preco_un),
                valor_total=_para_decimal(preco_total),
            )
        )

    return nf
