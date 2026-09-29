from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COR_CABECALHO = colors.HexColor("#171b26")
COR_BORDA = colors.HexColor("#e2e4e9")


def gerar_pdf_pedido(pedido):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(f"Pedido de Venda #{pedido.pk}", styles["Title"]))
    elementos.append(Paragraph(f"Status: {pedido.get_status_display()}", styles["Normal"]))
    elementos.append(Paragraph(f"Unidade: {pedido.unidade.nome}", styles["Normal"]))
    elementos.append(Paragraph(f"Data: {timezone.localtime(pedido.criado_em).strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elementos.append(Spacer(1, 8 * mm))

    cliente = pedido.cliente
    elementos.append(Paragraph("Cliente", styles["Heading3"]))
    elementos.append(Paragraph(cliente.nome, styles["Normal"]))
    elementos.append(Paragraph(f"CPF/CNPJ: {cliente.documento_formatado}", styles["Normal"]))
    if cliente.logradouro:
        endereco = f"{cliente.logradouro}, {cliente.numero} - {cliente.bairro}, {cliente.cidade}/{cliente.uf}"
        elementos.append(Paragraph(endereco, styles["Normal"]))
    if cliente.telefone:
        elementos.append(Paragraph(f"Telefone: {cliente.telefone}", styles["Normal"]))
    elementos.append(Spacer(1, 8 * mm))

    dados_tabela = [["Peça", "Qtde", "Preço un.", "Total"]]
    for item in pedido.itens.select_related("peca"):
        dados_tabela.append([
            item.peca.nome,
            str(item.quantidade),
            f"R$ {item.preco_unitario:.2f}",
            f"R$ {item.valor_total:.2f}",
        ])

    tabela = Table(dados_tabela, colWidths=[90 * mm, 20 * mm, 30 * mm, 30 * mm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, COR_BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 6 * mm))

    elementos.append(Paragraph(f"Subtotal: R$ {pedido.valor_produtos:.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Desconto: R$ {pedido.desconto:.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"<b>Total: R$ {pedido.valor_total:.2f}</b>", styles["Normal"]))

    if pedido.observacoes:
        elementos.append(Spacer(1, 8 * mm))
        elementos.append(Paragraph("Observações", styles["Heading3"]))
        elementos.append(Paragraph(pedido.observacoes, styles["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
