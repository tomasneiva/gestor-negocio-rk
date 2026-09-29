from django.urls import path

from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("tabela/", views.tabela, name="tabela"),
    path("pecas/", views.peca_lista, name="peca_lista"),
    path("pecas/nova/", views.peca_criar, name="peca_criar"),
    path("pecas/<int:pk>/editar/", views.peca_editar, name="peca_editar"),
]
