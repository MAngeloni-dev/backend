from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
)

from usuarios.models import Usuario


class PuedeGestionarInventario(BasePermission):
    message = (
        "Tu rol no tiene permiso para realizar esta operación."
    )

    def has_permission(self, request, view):
        usuario = request.user

        if (
            not usuario
            or not usuario.is_authenticated
            or not usuario.is_active
        ):
            return False

        roles_consulta = {
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.VETERINARIO,
            Usuario.Rol.RECEPCION,
        }

        roles_gestion = {
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.VETERINARIO,
        }

        if request.method in SAFE_METHODS:
            return usuario.rol in roles_consulta

        return usuario.rol in roles_gestion