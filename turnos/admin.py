from django.contrib import admin

from usuarios.models import Usuario

from .models import Turno


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = (
        "paciente",
        "veterinario",
        "inicio",
        "fin",
        "estado",
        "motivo",
    )

    list_filter = ("estado", "veterinario", "inicio")

    search_fields = (
        "paciente__nombre",
        "paciente__tutor__nombre",
        "paciente__tutor__apellido",
        "motivo",
    )

    autocomplete_fields = ("paciente",)
    list_select_related = ("paciente", "veterinario")

    readonly_fields = (
        "creado_por",
        "fecha_creacion",
        "fecha_actualizacion",
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "veterinario":
            kwargs["queryset"] = Usuario.objects.filter(
                is_active=True,
                rol__in=[
                    Usuario.Rol.ADMINISTRADOR,
                    Usuario.Rol.VETERINARIO,
                ],
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False