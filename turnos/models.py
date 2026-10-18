from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    DateTimeRangeField,
    RangeBoundary,
    RangeOperators,
)

class IntervaloTurno(models.Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()

class Turno(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        ATENDIDO = "ATENDIDO", "Atendido"
        CANCELADO = "CANCELADO", "Cancelado"

    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="turnos",
    )

    veterinario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="turnos_asignados",
    )

    inicio = models.DateTimeField()
    fin = models.DateTimeField()

    motivo = models.CharField(max_length=255)
    observaciones = models.TextField(blank=True)

    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="turnos_creados",
        editable=False,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["inicio", "id"]
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        indexes = [
            models.Index(
                fields=["veterinario", "inicio"],
                name="turno_vet_inicio_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fin__gt=models.F("inicio")),
                name="turno_fin_posterior_inicio",
            ),
            ExclusionConstraint(
                name="turno_sin_superposicion_profesional",
                expressions=[
                    (
                        IntervaloTurno(
                            "inicio",
                            "fin",
                            RangeBoundary(),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                    (
                        "veterinario",
                        RangeOperators.EQUAL,
                    ),
                ],
                condition=~models.Q(estado="CANCELADO"),
                violation_error_message=(
                    "El profesional ya tiene un turno en ese horario."
                ),
            ),
        ]

    def clean(self):
        super().clean()
        errores = {}

        anterior = None
        if not self._state.adding:
            anterior = (
                Turno.objects.filter(pk=self.pk)
                .values(
                    "paciente_id",
                    "veterinario_id",
                    "inicio",
                    "fin",
                    "estado",
                )
                .first()
            )

        nueva_reserva = self._state.adding or (
            anterior is not None
            and (
                anterior["paciente_id"] != self.paciente_id
                or anterior["veterinario_id"] != self.veterinario_id
                or anterior["inicio"] != self.inicio
                or anterior["fin"] != self.fin
                or (
                    anterior["estado"] == self.Estado.CANCELADO
                    and self.estado != self.Estado.CANCELADO
                )
            )
        )

        if self.inicio and self.fin:
            if self.fin <= self.inicio:
                errores["fin"] = (
                    "La hora de finalización debe ser posterior al inicio."
                )

        if nueva_reserva and self.estado != self.Estado.CANCELADO:
            if self.inicio and self.inicio <= timezone.now():
                errores["inicio"] = (
                    "Seleccioná una fecha y hora futuras."
                )

            if self.paciente_id:
                from pacientes.models import Paciente

                paciente = (
                    Paciente.objects.filter(pk=self.paciente_id)
                    .values("activo", "tutor__activo")
                    .first()
                )

                if paciente and (
                    not paciente["activo"] or not paciente["tutor__activo"]
                ):
                    errores["paciente"] = (
                        "El paciente y su tutor deben estar activos."
                    )

            if self.veterinario_id:
                from usuarios.models import Usuario

                profesional = (
                    Usuario.objects.filter(pk=self.veterinario_id)
                    .values("is_active", "rol")
                    .first()
                )

                if profesional and (
                    not profesional["is_active"]
                    or profesional["rol"] not in (
                        Usuario.Rol.ADMINISTRADOR,
                        Usuario.Rol.VETERINARIO,
                    )
                ):
                    errores["veterinario"] = (
                        "Seleccioná un Administrador o Veterinario activo."
                    )

        if (
            self.estado != self.Estado.CANCELADO
            and self.veterinario_id
            and self.inicio
            and self.fin
            and self.fin > self.inicio
        ):
            superpuestos = (
                Turno.objects.filter(
                    veterinario_id=self.veterinario_id,
                    inicio__lt=self.fin,
                    fin__gt=self.inicio,
                )
                .exclude(estado=self.Estado.CANCELADO)
            )

            if self.pk:
                superpuestos = superpuestos.exclude(pk=self.pk)

            if superpuestos.exists():
                errores["inicio"] = (
                    "El profesional ya tiene un turno en ese horario."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.paciente.nombre} — {self.motivo}"