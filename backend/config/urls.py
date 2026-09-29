from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.static import serve as serve_static


def healthcheck(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="estoque:painel", permanent=False)),
    path("admin/", admin.site.urls),
    path("health/", healthcheck),
    path("estoque/", include("estoque.urls")),
    path("clientes/", include("clientes.urls")),
    path("notas-fiscais/", include("notas_fiscais.urls")),
    path("media/<path:path>", serve_static, {"document_root": settings.MEDIA_ROOT}),
]
