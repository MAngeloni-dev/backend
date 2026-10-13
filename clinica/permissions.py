from rest_framework.permissions import BasePermission

from usuarios.models import Usuario


class PuedeGestionarConsultas(BasePermission):
    message = "Tu rol no tiene acceso a la historia clínica."

    def has_permission(self, request, view):
        usuario = request.user

        return (
            usuario.is_authenticated
            and usuario.is_active
            and usuario.rol in (
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            )
        )