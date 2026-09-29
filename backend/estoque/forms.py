from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import slugify

from .imaging import padronizar_imagem
from .models import Peca


class PecaForm(forms.ModelForm):
    preco = forms.DecimalField(
        label="Preço",
        localize=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.TextInput(attrs={
            "class": "campo-input",
            "inputmode": "decimal",
            "placeholder": "0,00",
        }),
    )

    class Meta:
        model = Peca
        fields = ["nome", "categoria", "preco", "imagem", "codigo", "codigo_externo"]
        labels = {
            "codigo": "Código interno (ref)",
            "codigo_externo": "Código externo",
        }
        help_texts = {
            "imagem": "A imagem é recortada no centro e padronizada para 1024x1024px (proporção 1:1).",
            "codigo_externo": "Até 13 dígitos numéricos.",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "campo-input"}),
            "categoria": forms.Select(attrs={"class": "campo-input"}),
            "imagem": forms.ClearableFileInput(attrs={"class": "campo-input", "accept": "image/*"}),
            "codigo": forms.TextInput(attrs={"class": "campo-input"}),
            "codigo_externo": forms.TextInput(attrs={
                "class": "campo-input",
                "inputmode": "numeric",
                "pattern": r"\d{1,13}",
                "maxlength": "13",
            }),
        }

    def save(self, commit=True):
        peca = super().save(commit=False)
        imagem = self.cleaned_data.get("imagem")
        if isinstance(imagem, UploadedFile):
            base = slugify(peca.nome) or "peca"
            peca.imagem = padronizar_imagem(imagem, nome_saida=f"{base}.jpg")
        if commit:
            peca.save()
        return peca
