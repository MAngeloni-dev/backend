from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)

from usuarios.models import Usuario

from .models import Lote, MovimientoStock


@transaction.atomic
def registrar_movimiento(
    *,
    lote_id,
    tipo,
    cantidad,
    motivo,
    responsable,
    observaciones="",
):
    roles_permitidos = {
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.VETERINARIO,
    }

    if (
        not responsable
        or not responsable.is_authenticated
        or not responsable.is_active
        or responsable.rol not in roles_permitidos
    ):
        raise PermissionDenied(
            "Tu rol no tiene permiso para modificar el stock."
        )

    if tipo not in MovimientoStock.Tipo.values:
        raise ValidationError(
            {"tipo": ["Seleccioná un tipo de movimiento válido."]}
        )

    # bool también es un subtipo de int en Python:
    # lo rechazamos explícitamente.
    if (
        isinstance(cantidad, bool)
        or not isinstance(cantidad, int)
        or cantidad <= 0
    ):
        raise ValidationError(
            {
                "cantidad": [
                    "Ingresá una cantidad entera mayor que cero."
                ]
            }
        )

    if not isinstance(motivo, str) or not motivo.strip():
        raise ValidationError(
            {"motivo": ["Ingresá el motivo del movimiento."]}
        )

    motivo = motivo.strip()

    if len(motivo) > 255:
        raise ValidationError(
            {
                "motivo": [
                    "El motivo no puede superar los 255 caracteres."
                ]
            }
        )

    if not isinstance(observaciones, str):
        raise ValidationError(
            {"observaciones": ["Ingresá un texto válido."]}
        )

    try:
        # El bloqueo se mantiene hasta finalizar la transacción.
        # Otro movimiento sobre este lote debe esperar.
        lote = (
            Lote.objects.select_related("medicamento")
            .select_for_update(of=("self",))
            .get(pk=lote_id)
        )
    except Lote.DoesNotExist as error:
        raise NotFound("El lote no existe.") from error

    tipos_entrada = {
        MovimientoStock.Tipo.INGRESO,
        MovimientoStock.Tipo.AJUSTE_ENTRADA,
    }

    operaciones_normales = {
        MovimientoStock.Tipo.INGRESO,
        MovimientoStock.Tipo.RETIRO,
    }

    # Los ajustes permiten corregir el inventario físico,
    # incluso de productos inactivos o vencidos.
    if tipo in operaciones_normales:
        if not lote.activo or not lote.medicamento.activo:
            raise ValidationError(
                {
                    "lote": [
                        "El lote y el medicamento deben estar activos."
                    ]
                }
            )

        if lote.fecha_vencimiento < timezone.localdate():
            raise ValidationError(
                {
                    "lote": [
                        "No se permiten ingresos ni retiros normales "
                        "sobre un lote vencido. "
                        "Usá un ajuste para registrar una corrección "
                        "o un descarte."
                    ]
                }
            )

    cantidad_anterior = lote.cantidad_actual

    if tipo in tipos_entrada:
        cantidad_posterior = cantidad_anterior + cantidad
    else:
        cantidad_posterior = cantidad_anterior - cantidad

    if cantidad_posterior < 0:
        raise ValidationError(
            {
                "cantidad": [
                    "No hay stock suficiente. "
                    f"Disponible: {cantidad_anterior} envases."
                ]
            }
        )

    # PositiveIntegerField utiliza un entero de 32 bits
    # en PostgreSQL.
    if cantidad_posterior > 2147483647:
        raise ValidationError(
            {
                "cantidad": [
                    "La cantidad resultante supera el máximo permitido."
                ]
            }
        )

    movimiento = MovimientoStock(
        lote=lote,
        tipo=tipo,
        cantidad=cantidad,
        cantidad_anterior=cantidad_anterior,
        cantidad_posterior=cantidad_posterior,
        responsable=responsable,
        motivo=motivo,
        observaciones=observaciones.strip(),
    )

    movimiento.save()

    lote.cantidad_actual = cantidad_posterior
    lote.save(
        update_fields=[
            "cantidad_actual",
            "fecha_actualizacion",
        ]
    )

    return movimiento