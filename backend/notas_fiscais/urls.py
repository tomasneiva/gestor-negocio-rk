from django.urls import path

from . import views

app_name = "notas_fiscais"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("enviar/", views.enviar, name="enviar"),
    path("enviar-lote/", views.enviar_lote, name="enviar_lote"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/produtos-pendentes/", views.produtos_pendentes, name="produtos_pendentes"),
]
