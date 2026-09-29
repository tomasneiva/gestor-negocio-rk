from django.urls import path

from . import views

app_name = "notas_fiscais"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("enviar/", views.enviar, name="enviar"),
    path("<int:pk>/editar/", views.editar, name="editar"),
]
