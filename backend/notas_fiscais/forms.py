from django import forms

from clientes.models import Cliente

from .models import NotaFiscal


class NotaFiscalUploadForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = ["arquivo"]
        widgets = {
            "arquivo": forms.ClearableFileInput(attrs={"class": "campo-input", "accept": "application/pdf"}),
        }


class NotaFiscalForm(forms.ModelForm):
    valor_produtos = forms.DecimalField(
        label="Valor dos produtos", localize=True, required=False, max_digits=12, decimal_places=2,
        widget=forms.TextInput(attrs={"class": "campo-input", "inputmode": "decimal"}),
    )
    desconto = forms.DecimalField(
        label="Desconto", localize=True, required=False, max_digits=12, decimal_places=2,
        widget=forms.TextInput(attrs={"class": "campo-input", "inputmode": "decimal"}),
    )
    valor_total = forms.DecimalField(
        label="Valor total", localize=True, required=True, max_digits=12, decimal_places=2,
        widget=forms.TextInput(attrs={"class": "campo-input", "inputmode": "decimal"}),
    )

    class Meta:
        model = NotaFiscal
        fields = [
            "cliente", "numero", "serie", "data_emissao",
            "valor_produtos", "desconto", "valor_total",
            "chave_acesso", "natureza_operacao", "observacoes",
        ]
        labels = {"cliente": "Cliente"}
        widgets = {
            "cliente": forms.Select(attrs={"class": "campo-input"}),
            "numero": forms.TextInput(attrs={"class": "campo-input"}),
            "serie": forms.TextInput(attrs={"class": "campo-input"}),
            "data_emissao": forms.DateInput(attrs={"class": "campo-input", "type": "date"}),
            "chave_acesso": forms.TextInput(attrs={"class": "campo-input", "inputmode": "numeric", "maxlength": 44}),
            "natureza_operacao": forms.TextInput(attrs={"class": "campo-input"}),
            "observacoes": forms.Textarea(attrs={"class": "campo-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.order_by("nome")
        self.fields["cliente"].required = True
        self.fields["numero"].required = True

    def clean_numero(self):
        numero = self.cleaned_data.get("numero", "").strip()
        if numero:
            existente = NotaFiscal.objects.filter(numero=numero).exclude(pk=self.instance.pk).first()
            if existente:
                raise forms.ValidationError(f"Já existe a nota fiscal #{existente.pk} com este número.")
        return numero
