from django.contrib import admin

from .models import Categoria, EstoqueItem, Peca, Unidade


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


class EstoqueItemInline(admin.TabularInline):
    model = EstoqueItem
    extra = 1


@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "preco", "codigo", "codigo_externo")
    list_filter = ("categoria",)
    search_fields = ("nome", "codigo", "codigo_externo")
    inlines = [EstoqueItemInline]


@admin.register(EstoqueItem)
class EstoqueItemAdmin(admin.ModelAdmin):
    list_display = ("peca", "unidade", "quantidade")
    list_filter = ("unidade", "peca__categoria")
    search_fields = ("peca__nome",)
