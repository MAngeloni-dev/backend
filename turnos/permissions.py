from rest_framework.permissions import BasePermission

from usuarios.models import Usuario


class PuedeGestionarTurnos(BasePermission):
    message = "Tu rol no tiene permiso para realizar esta operación."

    def has_permission(self, request, view):
        usuario = request.user

        if not usuario or not usuario.is_authenticated:
            return False

        if not usuario.is_active:
            return False

        roles_permitidos = {
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.VETERINARIO,
            Usuario.Rol.RECEPCION,
        }

        if usuario.rol not in roles_permitidos:
            return False

        if view.action == "atender":
            return usuario.rol in {
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            }

        return True