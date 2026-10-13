from django.contrib import admin

from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = (
        "paciente",
        "fecha",
        "veterinario",
        "motivo",
        "peso",
    )

    list_filter = ("fecha", "veterinario")
    search_fields = (
        "paciente__nombre",
        "paciente__tutor__nombre",
        "paciente__tutor__apellido",
        "motivo",
        "diagnostico",
    )

    autocomplete_fields = ("paciente", "veterinario")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    list_select_related = ("paciente", "veterinario")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "veterinario":
            from usuarios.models import Usuario

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

    def has_delete_permission(self, request, obj=None):
        return False