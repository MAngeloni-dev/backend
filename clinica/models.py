from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Consulta(models.Model):
    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="consultas",
    )

    veterinario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consultas_realizadas",
    )

    fecha = models.DateTimeField(default=timezone.now)

    motivo = models.CharField(
        max_length=255,
        verbose_name="Motivo de consulta",
    )

    sintomas = models.TextField(
        blank=True,
        verbose_name="Síntomas",
    )

    diagnostico = models.TextField(
        blank=True,
        verbose_name="Diagnóstico",
    )

    tratamiento = models.TextField(
        blank=True,
        verbose_name="Tratamiento indicado",
    )

    peso = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal("0.001")),
        ],
        verbose_name="Peso en kg",
    )

    observaciones = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"

    def clean(self):
        super().clean()
        errores = {}

        # La baja del paciente no impide consultar su historial.
        # Sí impide crear una nueva consulta.
        if self._state.adding and self.paciente_id:
            from pacientes.models import Paciente

            paciente_activo = (
                Paciente.objects.filter(pk=self.paciente_id)
                .values_list("activo", flat=True)
                .first()
            )

            if paciente_activo is False:
                errores["paciente"] = (
                    "No se pueden registrar consultas para un paciente inactivo."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.paciente.nombre} — {self.motivo}"