from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import EvolucionInternacion, Internacion


def validar_profesional(usuario):
    roles_permitidos = {
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.VETERINARIO,
    }

    if (
        not usuario
        or not usuario.is_authenticated
        or not usuario.is_active
        or usuario.rol not in roles_permitidos
    ):
        raise PermissionDenied(
            "Solo un administrador o veterinario activo "
            "puede realizar esta operación."
        )


def validar_modelo(instancia):
    try:
        instancia.full_clean()
    except DjangoValidationError as error:
        if hasattr(error, "message_dict"):
            detalle = {
                (
                    "non_field_errors"
                    if campo == "__all__"
                    else campo
                ): mensajes
                for campo, mensajes in error.message_dict.items()
            }
        else:
            detalle = {
                "non_field_errors": error.messages,
            }

        raise ValidationError(detalle) from error


@transaction.atomic
def abrir_internacion(
    *,
    paciente_id,
    veterinario_id,
    motivo,
    responsable,
    fecha_ingreso=None,
    diagnostico="",
    observaciones="",
):
    validar_profesional(responsable)

    try:
        # Serializa las aperturas para un mismo paciente.
        paciente = (
            Paciente.objects.select_related("tutor")
            .select_for_update(of=("self",))
            .get(pk=paciente_id)
        )
    except Paciente.DoesNotExist as error:
        raise NotFound("El paciente no existe.") from error

    if not paciente.activo or not paciente.tutor.activo:
        raise ValidationError(
            {
                "paciente": [
                    "El paciente y su tutor deben estar activos."
                ]
            }
        )

    if Internacion.objects.filter(
        paciente=paciente,
        estado=Internacion.Estado.INTERNADO,
    ).exists():
        raise ValidationError(
            {
                "paciente": [
                    "El paciente ya tiene una internación abierta."
                ]
            }
        )

    veterinario = Usuario.objects.filter(
        pk=veterinario_id,
        is_active=True,
        rol__in=[
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.VETERINARIO,
        ],
    ).first()

    if veterinario is None:
        raise ValidationError(
            {
                "veterinario": [
                    "Seleccioná un administrador "
                    "o veterinario activo."
                ]
            }
        )

    internacion = Internacion(
        paciente=paciente,
        veterinario=veterinario,
        motivo=motivo,
        diagnostico=diagnostico,
        observaciones=observaciones,
        fecha_ingreso=(
            fecha_ingreso
            if fecha_ingreso is not None
            else timezone.now()
        ),
        estado=Internacion.Estado.INTERNADO,
        creado_por=responsable,
    )

    validar_modelo(internacion)
    internacion.save()

    return internacion

@transaction.atomic
def cerrar_internacion(
    *,
    internacion_id,
    estado,
    responsable,
    fecha_egreso=None,
):
    validar_profesional(responsable)

    estados_cierre = {
        Internacion.Estado.ALTA,
        Internacion.Estado.FALLECIDO,
    }

    if estado not in estados_cierre:
        raise ValidationError(
            {
                "estado": [
                    "Seleccioná Alta o Fallecido para cerrar "
                    "la internación."
                ]
            }
        )

    try:
        internacion = (
            Internacion.objects.select_for_update()
            .get(pk=internacion_id)
        )
    except Internacion.DoesNotExist as error:
        raise NotFound(
            "La internación no existe."
        ) from error

    if internacion.estado != Internacion.Estado.INTERNADO:
        raise ValidationError(
            {
                "estado": [
                    "La internación ya está cerrada."
                ]
            }
        )

    fecha_cierre = (
        fecha_egreso
        if fecha_egreso is not None
        else timezone.now()
    )

    if internacion.evoluciones.filter(
        fecha__gt=fecha_cierre,
    ).exists():
        raise ValidationError(
            {
                "fecha_egreso": [
                    "El egreso no puede ser anterior "
                    "a un control ya registrado."
                ]
            }
        )

    internacion.estado = estado
    internacion.fecha_egreso = fecha_cierre

    validar_modelo(internacion)

    internacion.save(
        update_fields=[
            "estado",
            "fecha_egreso",
            "fecha_actualizacion",
        ]
    )

    return internacion


@transaction.atomic
def registrar_evolucion(
    *,
    internacion_id,
    responsable,
    observaciones,
    fecha=None,
    indicaciones="",
    peso=None,
    temperatura=None,
    frecuencia_cardiaca=None,
    frecuencia_respiratoria=None,
):
    validar_profesional(responsable)

    try:
        internacion = (
            Internacion.objects.select_for_update()
            .get(pk=internacion_id)
        )
    except Internacion.DoesNotExist as error:
        raise NotFound(
            "La internación no existe."
        ) from error

    if internacion.estado != Internacion.Estado.INTERNADO:
        raise ValidationError(
            {
                "internacion": [
                    "No se pueden agregar evoluciones "
                    "a una internación cerrada."
                ]
            }
        )

    evolucion = EvolucionInternacion(
        internacion=internacion,
        profesional=responsable,
        fecha=(
            fecha
            if fecha is not None
            else timezone.now()
        ),
        observaciones=observaciones,
        indicaciones=indicaciones,
        peso=peso,
        temperatura=temperatura,
        frecuencia_cardiaca=frecuencia_cardiaca,
        frecuencia_respiratoria=frecuencia_respiratoria,
    )

    validar_modelo(evolucion)
    evolucion.save()

    return evolucion