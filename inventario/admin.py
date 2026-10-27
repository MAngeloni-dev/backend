from django.contrib import admin
from django.utils import timezone

from .models import Lote, Medicamento, MovimientoStock
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import path, reverse
from rest_framework.exceptions import APIException

from usuarios.models import Usuario

from .forms import RegistrarMovimientoAdminForm
from .services import registrar_movimiento

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
        return (
            request.user.rol in {
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            }
            and request.user.has_perm(
                "inventario.add_movimientostock"
            )
    )

    def get_urls(self):
        urls_personalizadas = [
            path(
                "add/",
                self.admin_site.admin_view(
                    self.registrar_desde_admin
                ),
                name="inventario_movimientostock_add",
            ),
        ]

        return urls_personalizadas + super().get_urls()

    def registrar_desde_admin(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        form = RegistrarMovimientoAdminForm(
            request.POST if request.method == "POST" else None
        )

        if request.method == "POST" and form.is_valid():
            datos = form.cleaned_data

            try:
                movimiento = registrar_movimiento(
                    lote_id=datos["lote"].pk,
                    tipo=datos["tipo"],
                    cantidad=datos["cantidad"],
                    motivo=datos["motivo"],
                    observaciones=datos["observaciones"],
                    responsable=request.user,
                )
            except APIException as error:
                form.add_error(None, str(error.detail))
            else:
                self.log_addition(
                    request,
                    movimiento,
                    "Movimiento registrado desde el administrador.",
                )

                self.message_user(
                    request,
                    "Movimiento registrado y stock actualizado.",
                )

                return redirect(
                    reverse(
                        "admin:inventario_movimientostock_changelist",
                        current_app=self.admin_site.name,
                    )
                )

        contexto = {
            **self.admin_site.each_context(request),
            "title": "Registrar movimiento de stock",
            "opts": self.model._meta,
            "form": form,
            "url_volver": reverse(
                "admin:inventario_movimientostock_changelist",
                current_app=self.admin_site.name,
            ),
        }

        request.current_app = self.admin_site.name

        return render(
            request,
            "admin/inventario/registrar_movimiento.html",
            contexto,
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False