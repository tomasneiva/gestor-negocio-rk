from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models

from clientes.models import Cliente


class NotaFiscal(models.Model):
    arquivo = models.FileField(
        upload_to="notas_fiscais/",
        validators=[FileExtensionValidator(["pdf"])],
    )
    cliente = models.ForeignKey(
        Cliente, null=True, blank=True, on_delete=models.PROTECT, related_name="notas_fiscais"
    )
    numero = models.CharField(max_length=20, blank=True)
    serie = models.CharField(max_length=10, blank=True)
    data_emissao = models.DateField(null=True, blank=True)
    valor_produtos = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    chave_acesso = models.CharField(
        max_length=44,
        blank=True,
        validators=[RegexValidator(r"^\d{44}$", "Chave de acesso deve ter 44 dígitos.")],
    )
    natureza_operacao = models.CharField(max_length=200, blank=True)
    observacoes = models.TextField(blank=True)
    texto_extraido = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "nota fiscal"
        verbose_name_plural = "notas fiscais"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["numero"],
                condition=models.Q(numero__gt=""),
                name="notafiscal_numero_unico_quando_preenchido",
            ),
        ]

    def __str__(self):
        return f"NF {self.numero or '?'} - {self.cliente or 'sem cliente'}"


class NotaFiscalItem(models.Model):
    nota_fiscal = models.ForeignKey(NotaFiscal, on_delete=models.CASCADE, related_name="itens")
    codigo = models.CharField(max_length=50, blank=True)
    descricao = models.CharField(max_length=255, blank=True)
    ncm = models.CharField(max_length=20, blank=True)
    cfop = models.CharField(max_length=20, blank=True)
    unidade = models.CharField(max_length=10, blank=True)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "item da nota fiscal"
        verbose_name_plural = "itens da nota fiscal"

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
