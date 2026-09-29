from django.contrib import admin

from .models import NotaFiscal, NotaFiscalItem


class NotaFiscalItemInline(admin.TabularInline):
    model = NotaFiscalItem
    extra = 0


@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "data_emissao", "valor_total", "criado_em")
    list_filter = ("data_emissao",)
    search_fields = ("numero", "chave_acesso", "cliente__nome")
    inlines = [NotaFiscalItemInline]
