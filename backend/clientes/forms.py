from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "tipo_pessoa", "nome", "documento", "cep",
            "logradouro", "numero", "complemento", "bairro", "cidade", "uf",
            "telefone", "email", "nome_representante", "observacoes",
        ]
        labels = {"documento": "CPF/CNPJ"}
        widgets = {
            "tipo_pessoa": forms.RadioSelect(),
            "nome": forms.TextInput(attrs={"class": "campo-input"}),
            "documento": forms.TextInput(attrs={
                "class": "campo-input", "inputmode": "numeric", "placeholder": "Somente números",
            }),
            "cep": forms.TextInput(attrs={
                "class": "campo-input", "inputmode": "numeric", "placeholder": "00000-000", "id": "id_cep",
            }),
            "logradouro": forms.TextInput(attrs={"class": "campo-input", "id": "id_logradouro"}),
            "numero": forms.TextInput(attrs={"class": "campo-input"}),
            "complemento": forms.TextInput(attrs={"class": "campo-input", "id": "id_complemento"}),
            "bairro": forms.TextInput(attrs={"class": "campo-input", "id": "id_bairro"}),
            "cidade": forms.TextInput(attrs={"class": "campo-input", "id": "id_cidade"}),
            "uf": forms.TextInput(attrs={"class": "campo-input", "maxlength": 2, "id": "id_uf"}),
            "telefone": forms.TextInput(attrs={"class": "campo-input"}),
            "email": forms.EmailInput(attrs={"class": "campo-input"}),
            "nome_representante": forms.TextInput(attrs={"class": "campo-input"}),
            "observacoes": forms.Textarea(attrs={"class": "campo-input", "rows": 3}),
        }
