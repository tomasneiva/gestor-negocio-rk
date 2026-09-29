import io

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

TAMANHO_PADRAO = 1024


def padronizar_imagem(arquivo, nome_saida="peca.jpg"):
    """Recorta a imagem ao centro em proporção 1:1 e redimensiona para 1024x1024."""
    imagem = Image.open(arquivo)
    imagem = ImageOps.exif_transpose(imagem)

    if imagem.mode in ("RGBA", "LA", "P"):
        imagem = imagem.convert("RGBA")
        fundo = Image.new("RGB", imagem.size, (255, 255, 255))
        fundo.paste(imagem, mask=imagem.split()[-1])
        imagem = fundo
    else:
        imagem = imagem.convert("RGB")

    largura, altura = imagem.size
    lado = min(largura, altura)
    esquerda = (largura - lado) // 2
    topo = (altura - lado) // 2
    imagem = imagem.crop((esquerda, topo, esquerda + lado, topo + lado))
    imagem = imagem.resize((TAMANHO_PADRAO, TAMANHO_PADRAO), Image.LANCZOS)

    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=90)
    return ContentFile(buffer.getvalue(), name=nome_saida)
