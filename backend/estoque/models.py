from django.core.validators import RegexValidator
from django.db import models


class Unidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "unidade"
        verbose_name_plural = "unidades"
        ordering = ["id"]

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Peca(models.Model):
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="pecas")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem = models.ImageField(upload_to="pecas/", blank=True, null=True)
    codigo = models.CharField("código interno (ref)", max_length=50, blank=True)
    codigo_externo = models.CharField(
        "código externo",
        max_length=13,
        blank=True,
        validators=[RegexValidator(r"^\d{1,13}$", "Use apenas números, até 13 dígitos.")],
    )

    class Meta:
        verbose_name = "peça"
        verbose_name_plural = "peças"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class EstoqueItem(models.Model):
    peca = models.ForeignKey(Peca, on_delete=models.CASCADE, related_name="estoque_itens")
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name="estoque_itens")
    quantidade = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "item de estoque"
        verbose_name_plural = "itens de estoque"
        constraints = [
            models.UniqueConstraint(fields=["peca", "unidade"], name="unico_peca_por_unidade")
        ]

    def __str__(self):
        return f"{self.peca} @ {self.unidade}: {self.quantidade}"
