from django.contrib import admin

from .models import Especie, Paciente, Raza, Tutor


class PacienteInline(admin.TabularInline):
    model = Paciente
    fields = ("nombre", "especie", "raza", "sexo", "activo")
    extra = 0
    show_change_link = True
    can_delete = False


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = (
        "apellido",
        "nombre",
        "telefono",
        "email",
        "activo",
    )
    search_fields = ("nombre", "apellido", "dni", "telefono", "email")
    list_filter = ("activo",)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    inlines = [PacienteInline]


@admin.register(Especie)
class EspecieAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(Raza)
class RazaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "especie", "activo")
    search_fields = ("nombre", "especie__nombre")
    list_filter = ("especie", "activo")
    autocomplete_fields = ("especie",)


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "tutor",
        "especie",
        "raza",
        "sexo",
        "activo",
    )
    search_fields = (
        "nombre",
        "microchip",
        "tutor__nombre",
        "tutor__apellido",
    )
    list_filter = ("especie", "sexo", "activo")
    autocomplete_fields = ("tutor", "especie", "raza")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    list_select_related = ("tutor", "especie", "raza")