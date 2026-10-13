from django.urls import path

from .views import UsuarioActualView


urlpatterns = [
    path("me/", UsuarioActualView.as_view(), name="usuario_actual"),
]