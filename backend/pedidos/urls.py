from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/confirmar/", views.confirmar, name="confirmar"),
    path("<int:pk>/cancelar/", views.cancelar, name="cancelar"),
    path("<int:pk>/baixa-estoque/", views.baixar_estoque, name="baixa_estoque"),
    path("<int:pk>/desfazer-baixa/", views.desfazer_baixa, name="desfazer_baixa"),
    path("<int:pk>/pdf/", views.pdf, name="pdf"),
]
