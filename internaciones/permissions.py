from rest_framework.permissions import BasePermission

from usuarios.models import Usuario


class PuedeGestionarInternaciones(BasePermission):
    message = (
        "Solo administrador y veterinario pueden "
        "acceder a las internaciones."
    )

    def has_permission(self, request, view):
        usuario = request.user

        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.is_active
            and usuario.rol in {
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            }
        )