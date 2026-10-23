from django.contrib import admin
from django.utils import timezone

from .models import Lote, Medicamento, MovimientoStock


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "laboratorio",
        "concentracion",
        "presentacion",
        "stock_minimo",
        "activo",
    ]

    list_filter = [
        "activo",
        "via_administracion",
        "especies",
    ]

    search_fields = [
        "nombre",
        "laboratorio",
        "principio_activo",
        "codigo_barras",
    ]

    ordering = ["nombre", "id"]

    filter_horizontal = ["especies"]

    readonly_fields = [
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    actions = ["desactivar_medicamentos"]

    @admin.action(description="Dar de baja los medicamentos seleccionados")
    def desactivar_medicamentos(self, request, queryset):
        cantidad = queryset.update(
            activo=False,
            fecha_actualizacion=timezone.now(),
        )

        self.message_user(
            request,
            f"Medicamentos dados de baja: {cantidad}.",
        )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = [
        "numero",
        "medicamento",
        "fecha_vencimiento",
        "cantidad_actual",
        "activo",
    ]

    list_filter = [
        "activo",
        "fecha_vencimiento",
    ]

    search_fields = [
        "numero",
        "medicamento__nombre",
        "medicamento__codigo_barras",
    ]

    ordering = ["fecha_vencimiento", "id"]

    autocomplete_fields = ["medicamento"]

    list_select_related = ["medicamento"]

    readonly_fields = [
        "cantidad_actual",
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    actions = ["desactivar_lotes"]

    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))

        if obj is not None:
            campos.append("medicamento")

        return campos

    @admin.action(description="Dar de baja los lotes seleccionados")
    def desactivar_lotes(self, request, queryset):
        cantidad = queryset.update(
            activo=False,
            fecha_actualizacion=timezone.now(),
        )

        self.message_user(
            request,
            f"Lotes dados de baja: {cantidad}.",
        )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "lote",
        "tipo",
        "cantidad",
        "cantidad_anterior",
        "cantidad_posterior",
        "responsable",
        "fecha_creacion",
    ]

    list_filter = [
        "tipo",
        "fecha_creacion",
        "responsable",
    ]

    search_fields = [
        "lote__numero",
        "lote__medicamento__nombre",
        "motivo",
        "responsable__username",
    ]

    ordering = ["-fecha_creacion", "-id"]

    date_hierarchy = "fecha_creacion"

    list_select_related = [
        "lote",
        "lote__medicamento",
        "responsable",
    ]

    readonly_fields = [
        "lote",
        "tipo",
        "cantidad",
        "cantidad_anterior",
        "cantidad_posterior",
        "responsable",
        "motivo",
        "observaciones",
        "fecha_creacion",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False