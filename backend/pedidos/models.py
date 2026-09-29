from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from clientes.models import Cliente
from estoque.models import EstoqueItem, Peca, Unidade


class PedidoVenda(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = "RASCUNHO", "Rascunho"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        CANCELADO = "CANCELADO", "Cancelado"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="pedidos_venda")
    unidade = models.ForeignKey(Unidade, on_delete=models.PROTECT, related_name="pedidos_venda")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RASCUNHO)
    desconto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)
    confirmado_em = models.DateTimeField(null=True, blank=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)
    baixa_estoque_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "pedido de venda"
        verbose_name_plural = "pedidos de venda"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Pedido #{self.pk or '?'} - {self.cliente}"

    @property
    def valor_produtos(self):
        return sum((item.valor_total for item in self.itens.all()), Decimal("0"))

    @property
    def valor_total(self):
        return self.valor_produtos - self.desconto

    @property
    def pode_editar(self):
        return self.status == self.Status.RASCUNHO

    @property
    def pode_confirmar(self):
        return self.status == self.Status.RASCUNHO

    @property
    def pode_cancelar(self):
        return self.status in (self.Status.RASCUNHO, self.Status.CONFIRMADO)

    @property
    def pode_dar_baixa(self):
        return self.status == self.Status.CONFIRMADO and self.baixa_estoque_em is None

    @property
    def pode_desfazer_baixa(self):
        return self.baixa_estoque_em is not None

    def confirmar(self):
        if not self.pode_confirmar:
            raise ValidationError("Só é possível confirmar pedidos em rascunho.")
        if not self.itens.exists():
            raise ValidationError("Adicione ao menos um item antes de confirmar.")
        self.status = self.Status.CONFIRMADO
        self.confirmado_em = timezone.now()
        self.save(update_fields=["status", "confirmado_em"])

    def cancelar(self):
        if not self.pode_cancelar:
            raise ValidationError("Este pedido não pode mais ser cancelado.")
        if self.baixa_estoque_em is not None:
            self.desfazer_baixa_estoque()
        self.status = self.Status.CANCELADO
        self.cancelado_em = timezone.now()
        self.save(update_fields=["status", "cancelado_em"])

    def dar_baixa_estoque(self):
        if not self.pode_dar_baixa:
            raise ValidationError("Só é possível dar baixa em pedidos confirmados que ainda não tiveram baixa lançada.")
        avisos = []
        with transaction.atomic():
            for item in self.itens.select_related("peca").select_for_update():
                estoque_item, _ = EstoqueItem.objects.select_for_update().get_or_create(
                    peca=item.peca, unidade=self.unidade, defaults={"quantidade": 0}
                )
                baixado = min(item.quantidade, estoque_item.quantidade)
                if baixado < item.quantidade:
                    avisos.append(
                        f"{item.peca.nome}: faltam {item.quantidade - baixado} unidade(s) em estoque "
                        f"(baixado {baixado} de {item.quantidade})."
                    )
                estoque_item.quantidade -= baixado
                estoque_item.save(update_fields=["quantidade"])
                item.quantidade_baixada = baixado
                item.save(update_fields=["quantidade_baixada"])
            self.baixa_estoque_em = timezone.now()
            self.save(update_fields=["baixa_estoque_em"])
        return avisos

    def desfazer_baixa_estoque(self):
        if self.baixa_estoque_em is None:
            return
        with transaction.atomic():
            for item in self.itens.select_related("peca").select_for_update():
                if item.quantidade_baixada:
                    estoque_item, _ = EstoqueItem.objects.select_for_update().get_or_create(
                        peca=item.peca, unidade=self.unidade, defaults={"quantidade": 0}
                    )
                    estoque_item.quantidade += item.quantidade_baixada
                    estoque_item.save(update_fields=["quantidade"])
                    item.quantidade_baixada = None
                    item.save(update_fields=["quantidade_baixada"])
            self.baixa_estoque_em = None
            self.save(update_fields=["baixa_estoque_em"])


class PedidoVendaItem(models.Model):
    pedido = models.ForeignKey(PedidoVenda, on_delete=models.CASCADE, related_name="itens")
    peca = models.ForeignKey(Peca, on_delete=models.PROTECT, related_name="itens_pedido_venda")
    quantidade = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_baixada = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    def __str__(self):
        return f"{self.peca} x{self.quantidade}"

    @property
    def valor_total(self):
        return self.preco_unitario * self.quantidade
