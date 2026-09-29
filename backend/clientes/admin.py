from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_pessoa", "documento", "cidade", "uf", "telefone", "email")
    list_filter = ("tipo_pessoa", "uf")
    search_fields = ("nome", "documento", "email")
