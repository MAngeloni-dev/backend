from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Internacion(models.Model):
    class Estado(models.TextChoices):
        INTERNADO = "INTERNADO", "Internado"
        ALTA = "ALTA", "Alta"
        FALLECIDO = "FALLECIDO", "Fallecido"

    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="internaciones",
    )

    veterinario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internaciones_a_cargo",
    )

    fecha_ingreso = models.DateTimeField(
        default=timezone.now,
    )

    fecha_egreso = models.DateTimeField(
        null=True,
        blank=True,
    )

    motivo = models.CharField(
        max_length=255,
    )

    diagnostico = models.TextField(
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
    )

    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.INTERNADO,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internaciones_creadas",
        editable=False,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-fecha_ingreso", "-id"]
        verbose_name = "Internación"
        verbose_name_plural = "Internaciones"

        constraints = [
            models.UniqueConstraint(
                fields=["paciente"],
                condition=models.Q(estado="INTERNADO"),
                name="internacion_activa_unica_paciente",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        estado="INTERNADO",
                        fecha_egreso__isnull=True,
                    )
                    | models.Q(
                        estado__in=["ALTA", "FALLECIDO"],
                        fecha_egreso__isnull=False,
                        fecha_egreso__gte=models.F("fecha_ingreso"),
                    )
                ),
                name="internacion_estado_egreso_coherente",
            ),
        ]

    def clean(self):
        super().clean()

        errores = {}

        self.motivo = (self.motivo or "").strip()

        if not self.motivo:
            errores["motivo"] = (
                "Ingresá el motivo de la internación."
            )

        ahora = timezone.now()

        if self.fecha_ingreso and self.fecha_ingreso > ahora:
            errores["fecha_ingreso"] = (
                "La fecha de ingreso no puede ser futura."
            )

        if self.fecha_egreso:
            if self.fecha_egreso > ahora:
                errores["fecha_egreso"] = (
                    "La fecha de egreso no puede ser futura."
                )

            if (
                self.fecha_ingreso
                and self.fecha_egreso < self.fecha_ingreso
            ):
                errores["fecha_egreso"] = (
                    "El egreso no puede ser anterior al ingreso."
                )

        if self.estado == self.Estado.INTERNADO:
            if self.fecha_egreso is not None:
                errores["fecha_egreso"] = (
                    "Una internación abierta no debe tener egreso."
                )

        elif self.estado in {
            self.Estado.ALTA,
            self.Estado.FALLECIDO,
        }:
            if self.fecha_egreso is None:
                errores["fecha_egreso"] = (
                    "Registrá la fecha de egreso."
                )

        else:
            errores["estado"] = (
                "Seleccioná un estado válido."
            )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"Internación de {self.paciente.nombre} — "
            f"{self.get_estado_display()}"
        )

class EvolucionInternacion(models.Model):
    internacion = models.ForeignKey(
        Internacion,
        on_delete=models.PROTECT,
        related_name="evoluciones",
    )

    profesional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evoluciones_internacion",
        editable=False,
    )

    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha del control",
    )

    peso = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Peso en kilogramos.",
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Temperatura en grados Celsius.",
    )

    frecuencia_cardiaca = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Latidos por minuto.",
    )

    frecuencia_respiratoria = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Respiraciones por minuto.",
    )

    observaciones = models.TextField()

    indicaciones = models.TextField(
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Evolución de internación"
        verbose_name_plural = "Evoluciones de internación"

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(peso__isnull=True)
                    | models.Q(peso__gt=0)
                ),
                name="evolucion_peso_positivo",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(frecuencia_cardiaca__isnull=True)
                    | models.Q(frecuencia_cardiaca__gt=0)
                ),
                name="evolucion_fc_positiva",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(frecuencia_respiratoria__isnull=True)
                    | models.Q(frecuencia_respiratoria__gt=0)
                ),
                name="evolucion_fr_positiva",
            ),
        ]

    def clean(self):
        super().clean()

        errores = {}

        self.observaciones = (
            self.observaciones or ""
        ).strip()

        if not self.observaciones:
            errores["observaciones"] = (
                "Registrá las observaciones del control."
            )

        if self.fecha:
            if self.fecha > timezone.now():
                errores["fecha"] = (
                    "La fecha del control no puede ser futura."
                )

            if self.internacion_id:
                internacion = (
                    Internacion.objects.filter(
                        pk=self.internacion_id
                    )
                    .values(
                        "fecha_ingreso",
                        "fecha_egreso",
                    )
                    .first()
                )

                if internacion:
                    if self.fecha < internacion["fecha_ingreso"]:
                        errores["fecha"] = (
                            "El control no puede ser anterior "
                            "al ingreso del paciente."
                        )

                    egreso = internacion["fecha_egreso"]

                    if egreso and self.fecha > egreso:
                        errores["fecha"] = (
                            "El control no puede ser posterior "
                            "al egreso del paciente."
                        )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"Evolución de internación "
            f"{self.internacion_id} — {self.fecha}"
        )