from django.urls import path

from .views import ProfesionalListView, UsuarioActualView


urlpatterns = [
    path(
        "me/",
        UsuarioActualView.as_view(),
        name="usuario_actual",
    ),
    path(
        "profesionales/",
        ProfesionalListView.as_view(),
        name="profesional_list",
    ),
]