from django import forms
from django.forms import inlineformset_factory

from .models import PedidoVenda, PedidoVendaItem


class PecaSelectComPreco(forms.Select):
    def __init__(self, precos=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.precos = precos or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        preco = self.precos.get(value)
        if preco is not None:
            option["attrs"]["data-preco"] = str(preco)
        return option


class PedidoVendaForm(forms.ModelForm):
    desconto = forms.DecimalField(
        label="Desconto", localize=True, required=False, max_digits=12, decimal_places=2,
        widget=forms.TextInput(attrs={"class": "campo-input", "inputmode": "decimal", "placeholder": "0,00"}),
    )

    class Meta:
        model = PedidoVenda
        fields = ["cliente", "unidade", "desconto", "observacoes"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "campo-input"}),
            "unidade": forms.Select(attrs={"class": "campo-input"}),
            "observacoes": forms.Textarea(attrs={"class": "campo-input", "rows": 3}),
        }


class PedidoVendaItemForm(forms.ModelForm):
    quantidade = forms.IntegerField(
        label="Quantidade", min_value=1, initial=1,
        widget=forms.NumberInput(attrs={"class": "campo-input campo-qtd"}),
    )
    preco_unitario = forms.DecimalField(
        label="Preço unitário", localize=True, max_digits=10, decimal_places=2,
        widget=forms.TextInput(attrs={"class": "campo-input campo-preco", "inputmode": "decimal"}),
    )

    class Meta:
        model = PedidoVendaItem
        fields = ["peca", "quantidade", "preco_unitario"]

    def __init__(self, *args, precos=None, **kwargs):
        super().__init__(*args, **kwargs)
        widget = PecaSelectComPreco(precos=precos, attrs={"class": "campo-input peca-select"})
        widget.choices = self.fields["peca"].choices
        self.fields["peca"].widget = widget


PedidoVendaItemFormSet = inlineformset_factory(
    PedidoVenda,
    PedidoVendaItem,
    form=PedidoVendaItemForm,
    extra=3,
    can_delete=True,
)
