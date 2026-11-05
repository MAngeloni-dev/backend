from django.urls import path

from .views import (
    ActualizarPerfilView,
    CambiarPasswordView,
    ProfesionalListView,
    UsuarioActualView,
)


urlpatterns = [
    path(
        "me/",
        UsuarioActualView.as_view(),
        name="usuario_actual",
    ),
    path(
        "me/perfil/",
        ActualizarPerfilView.as_view(),
        name="actualizar_perfil",
    ),
    path(
        "me/password/",
        CambiarPasswordView.as_view(),
        name="cambiar_password",
    ),
    path(
        "profesionales/",
        ProfesionalListView.as_view(),
        name="profesional_list",
    ),
]