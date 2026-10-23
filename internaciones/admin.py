from django.contrib import admin
from django.utils.html import format_html
from .models import EvolucionInternacion, Internacion
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import path, reverse
from rest_framework.exceptions import APIException

from .forms import (
    AbrirInternacionAdminForm,
    CerrarInternacionAdminForm,
    RegistrarEvolucionAdminForm,
)

from .services import (
    abrir_internacion,
    cerrar_internacion,
    registrar_evolucion,
)
from usuarios.models import Usuario

class EvolucionInline(admin.TabularInline):
    model = EvolucionInternacion
    extra = 0

    fields = [
        "fecha",
        "profesional",
        "observaciones",
    ]

    readonly_fields = fields

    show_change_link = True
    can_delete = False

    ordering = ["-fecha", "-id"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Internacion)
class InternacionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "paciente",
        "veterinario",
        "estado",
        "fecha_ingreso",
        "fecha_egreso",
    ]

    list_filter = [
        "estado",
        "veterinario",
        "fecha_ingreso",
    ]

    search_fields = [
        "paciente__nombre",
        "paciente__tutor__nombre",
        "paciente__tutor__apellido",
        "motivo",
        "diagnostico",
    ]

    ordering = ["-fecha_ingreso", "-id"]

    date_hierarchy = "fecha_ingreso"

    list_select_related = [
        "paciente",
        "veterinario",
        "creado_por",
    ]

    readonly_fields = [
        "paciente",
        "veterinario",
        "fecha_ingreso",
        "fecha_egreso",
        "motivo",
        "diagnostico",
        "observaciones",
        "estado",
        "creado_por",
        "fecha_creacion",
        "fecha_actualizacion",
        "acciones_internacion",
    ]

    inlines = [EvolucionInline]

    def has_add_permission(self, request):
        return (
            request.user.rol in {
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            }
            and request.user.has_perm(
                "internaciones.add_internacion"
            )
        )

    def get_urls(self):
        urls_personalizadas = [
            path(
                "add/",
                self.admin_site.admin_view(
                    self.abrir_desde_admin
                ),
                name="internaciones_internacion_add",
            ),
            path(
                "<int:object_id>/cerrar/",
                self.admin_site.admin_view(
                    self.cerrar_desde_admin
                ),
                name="internaciones_internacion_cerrar",
            ),
        ]

        return urls_personalizadas + super().get_urls()

    @admin.display(description="Acciones")
    def acciones_internacion(self, obj):
        if obj.estado != Internacion.Estado.INTERNADO:
            return "Internación cerrada."

        url = reverse(
            "admin:internaciones_internacion_cerrar",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )

        return format_html(
            '<a class="button" href="{}">'
            "Cerrar internación"
            "</a>",
            url,
        )

    def cerrar_desde_admin(self, request, object_id):
        puede_cerrar = (
            request.user.rol in {
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            }
            and request.user.has_perm(
                "internaciones.change_internacion"
            )
        )

        if not puede_cerrar:
            raise PermissionDenied

        internacion = self.get_object(
            request,
            str(object_id),
        )

        if internacion is None:
            from django.http import Http404

            raise Http404("La internación no existe.")

        if not self.has_view_permission(
            request,
            internacion,
        ):
            raise PermissionDenied

        url_detalle = reverse(
            "admin:internaciones_internacion_change",
            args=[internacion.pk],
            current_app=self.admin_site.name,
        )

        form = CerrarInternacionAdminForm(
            request.POST if request.method == "POST" else None
        )

        if request.method == "POST" and form.is_valid():
            try:
                internacion = cerrar_internacion(
                    internacion_id=internacion.pk,
                    estado=form.cleaned_data["estado"],
                    responsable=request.user,
                )
            except APIException as error:
                form.add_error(None, str(error.detail))
            else:
                self.log_change(
                    request,
                    internacion,
                    (
                        "Internación cerrada desde el administrador. "
                        f"Estado: {internacion.estado}."
                    ),
                )

                self.message_user(
                    request,
                    "Internación cerrada correctamente.",
                )

                return redirect(url_detalle)

        contexto = {
            **self.admin_site.each_context(request),
            "title": "Cerrar internación",
            "opts": self.model._meta,
            "form": form,
            "internacion": internacion,
            "url_detalle": url_detalle,
        }

        request.current_app = self.admin_site.name

        return render(
            request,
            "admin/internaciones/cerrar_internacion.html",
            contexto,
        )
    
    def abrir_desde_admin(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        form = AbrirInternacionAdminForm(
            request.POST if request.method == "POST" else None
        )

        if request.method == "POST" and form.is_valid():
            datos = form.cleaned_data

            try:
                internacion = abrir_internacion(
                    paciente_id=datos["paciente"].pk,
                    veterinario_id=datos["veterinario"].pk,
                    motivo=datos["motivo"],
                    diagnostico=datos["diagnostico"],
                    observaciones=datos["observaciones"],
                    responsable=request.user,
                )
            except APIException as error:
                form.add_error(
                    None,
                    str(error.detail),
                )
            else:
                self.log_addition(
                    request,
                    internacion,
                    "Internación abierta desde el administrador.",
                )

                self.message_user(
                    request,
                    "Internación registrada correctamente.",
                )

                return redirect(
                    reverse(
                        "admin:internaciones_internacion_change",
                        args=[internacion.pk],
                        current_app=self.admin_site.name,
                    )
                )

        contexto = {
            **self.admin_site.each_context(request),
            "title": "Abrir internación",
            "opts": self.model._meta,
            "form": form,
            "media": form.media,
        }

        request.current_app = self.admin_site.name

        return render(
            request,
            "admin/internaciones/abrir_internacion.html",
            contexto,
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EvolucionInternacion)
class EvolucionInternacionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "internacion",
        "profesional",
        "fecha",
        "peso",
        "temperatura",
    ]

    list_filter = [
        "profesional",
        "fecha",
    ]

    search_fields = [
        "internacion__paciente__nombre",
        "observaciones",
        "indicaciones",
    ]

    ordering = ["-fecha", "-id"]

    date_hierarchy = "fecha"

    list_select_related = [
        "internacion",
        "internacion__paciente",
        "profesional",
    ]

    readonly_fields = [
        "internacion",
        "profesional",
        "fecha",
        "peso",
        "temperatura",
        "frecuencia_cardiaca",
        "frecuencia_respiratoria",
        "observaciones",
        "indicaciones",
        "fecha_creacion",
    ]

    def has_add_permission(self, request):
        return (
            request.user.rol in {
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            }
            and request.user.has_perm(
                "internaciones.add_evolucioninternacion"
            )
        )

    def get_urls(self):
        urls_personalizadas = [
            path(
                "add/",
                self.admin_site.admin_view(
                    self.registrar_desde_admin
                ),
                name=(
                    "internaciones_"
                    "evolucioninternacion_add"
                ),
            ),
        ]

        return urls_personalizadas + super().get_urls()

    def registrar_desde_admin(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        form = RegistrarEvolucionAdminForm(
            request.POST if request.method == "POST" else None
        )

        if request.method == "POST" and form.is_valid():
            datos = form.cleaned_data

            try:
                evolucion = registrar_evolucion(
                    internacion_id=datos["internacion"].pk,
                    responsable=request.user,
                    observaciones=datos["observaciones"],
                    indicaciones=datos["indicaciones"],
                    peso=datos["peso"],
                    temperatura=datos["temperatura"],
                    frecuencia_cardiaca=datos[
                        "frecuencia_cardiaca"
                    ],
                    frecuencia_respiratoria=datos[
                        "frecuencia_respiratoria"
                    ],
                )
            except APIException as error:
                form.add_error(None, str(error.detail))
            else:
                self.log_addition(
                    request,
                    evolucion,
                    "Evolución registrada desde el administrador.",
                )

                self.message_user(
                    request,
                    "Evolución registrada correctamente.",
                )

                return redirect(
                    reverse(
                        (
                            "admin:internaciones_"
                            "evolucioninternacion_changelist"
                        ),
                        current_app=self.admin_site.name,
                    )
                )

        contexto = {
            **self.admin_site.each_context(request),
            "title": "Registrar evolución",
            "opts": self.model._meta,
            "form": form,
            "url_volver": reverse(
                (
                    "admin:internaciones_"
                    "evolucioninternacion_changelist"
                ),
                current_app=self.admin_site.name,
            ),
        }

        request.current_app = self.admin_site.name

        return render(
            request,
            "admin/internaciones/registrar_evolucion.html",
            contexto,
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False