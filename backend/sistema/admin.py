from django.contrib import admin

from .models import VersaoSistema


@admin.register(VersaoSistema)
class VersaoSistemaAdmin(admin.ModelAdmin):
    list_display = ("numero", "descricao", "implantado_em")
    ordering = ("-implantado_em",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
