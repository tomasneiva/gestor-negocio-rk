from django.contrib import admin

from .models import PedidoVenda, PedidoVendaItem


class PedidoVendaItemInline(admin.TabularInline):
    model = PedidoVendaItem
    extra = 1


@admin.register(PedidoVenda)
class PedidoVendaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "unidade", "status", "criado_em")
    list_filter = ("status", "unidade")
    search_fields = ("cliente__nome",)
    inlines = [PedidoVendaItemInline]
