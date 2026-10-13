from rest_framework.permissions import BasePermission

from .models import Usuario


class PuedeGestionarTutoresPacientes(BasePermission):
    message = "Tu rol no tiene permiso para realizar esta operación."

    def has_permission(self, request, view):
        usuario = request.user

        if not usuario.is_authenticated or not usuario.is_active:
            return False

        if usuario.rol in (
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.VETERINARIO,
        ):
            return True

        if usuario.rol != Usuario.Rol.RECEPCION:
            return False

        if view.action == "create":
            # Recepción solamente puede crear registros activos.
            activo = request.data.get("activo", True)
            return str(activo).lower() in ("true", "1")

        return view.action in (
            "list",
            "retrieve",
            "update",
            "partial_update",
            "metadata",
        )

    def has_object_permission(self, request, view, obj):
        if request.user.rol != Usuario.Rol.RECEPCION:
            return True

        # Evitar que Recepción cambie el estado mediante PUT/PATCH.
        if "activo" in request.data:
            activo = str(request.data["activo"]).lower()

            if activo not in ("true", "false", "1", "0"):
                return False

            nuevo_estado = activo in ("true", "1")

            if nuevo_estado != obj.activo:
                return False

        return True