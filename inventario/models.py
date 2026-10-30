from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.conf import settings

class Medicamento(models.Model):
    class ViaAdministracion(models.TextChoices):
        ORAL = "ORAL", "Oral"
        SUBCUTANEA = "SUBCUTANEA", "Subcutánea"
        INTRAMUSCULAR = "INTRAMUSCULAR", "Intramuscular"
        INTRAVENOSA = "INTRAVENOSA", "Intravenosa"
        TOPICA = "TOPICA", "Tópica"
        OFTALMICA = "OFTALMICA", "Oftálmica"
        OTICA = "OTICA", "Ótica"
        OTRA = "OTRA", "Otra"

    class UnidadContenido(models.TextChoices):
        ML = "ML", "Mililitros"
        G = "G", "Gramos"
        COMPRIMIDO = "COMPRIMIDO", "Comprimidos"
        CAPSULA = "CAPSULA", "Cápsulas"
        DOSIS = "DOSIS", "Dosis"
        UNIDAD = "UNIDAD", "Unidades"

    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre comercial",
    )

    laboratorio = models.CharField(
        max_length=150,
        blank=True,
    )

    principio_activo = models.CharField(
        max_length=200,
    )

    concentracion = models.CharField(
        max_length=100,
        help_text="Por ejemplo: 50 mg/ml o 500 mg.",
    )

    presentacion = models.CharField(
        max_length=100,
        help_text="Por ejemplo: frasco, caja o pomo.",
    )

    contenido_neto = models.DecimalField(
        max_digits=10,
        decimal_places=3,
    )

    unidad_contenido = models.CharField(
        max_length=12,
        choices=UnidadContenido.choices,
    )

    codigo_barras = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    via_administracion = models.CharField(
        max_length=15,
        choices=ViaAdministracion.choices,
    )

    especies = models.ManyToManyField(
        "pacientes.Especie",
        related_name="medicamentos",
        blank=True,
    )

    stock_minimo = models.PositiveIntegerField(
        default=0,
        help_text="Cantidad mínima de envases completos.",
    )

    observaciones = models.TextField(
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["nombre", "id"]
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"

        constraints = [
            models.CheckConstraint(
                condition=models.Q(contenido_neto__gt=0),
                name="medicamento_contenido_positivo",
            ),
            models.UniqueConstraint(
                Lower("nombre"),
                Lower("laboratorio"),
                Lower("concentracion"),
                Lower("presentacion"),
                "contenido_neto",
                "unidad_contenido",
                name="medicamento_presentacion_unica",
            ),
        ]

    def clean(self):
        super().clean()

        errores = {}

        campos_obligatorios = [
            "nombre",
            "principio_activo",
            "concentracion",
            "presentacion",
        ]

        for campo in campos_obligatorios:
            valor = getattr(self, campo, "")
            valor = (valor or "").strip()
            setattr(self, campo, valor)

            if not valor:
                errores[campo] = "Este campo es obligatorio."

        self.laboratorio = (self.laboratorio or "").strip()

        self.codigo_barras = (
            (self.codigo_barras or "").strip() or None
        )

        if (
            self.contenido_neto is not None
            and self.contenido_neto <= 0
        ):
            errores["contenido_neto"] = (
                "El contenido neto debe ser mayor que cero."
            )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"{self.nombre} — {self.concentracion} — "
            f"{self.presentacion} "
            f"{self.contenido_neto} "
            f"{self.get_unidad_contenido_display()}"
        )

class Lote(models.Model):
    medicamento = models.ForeignKey(
        Medicamento,
        on_delete=models.PROTECT,
        related_name="lotes",
    )

    numero = models.CharField(
        max_length=100,
        verbose_name="Número de lote",
    )

    fecha_vencimiento = models.DateField()

    cantidad_actual = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Cantidad de envases completos disponibles.",
    )

    observaciones = models.TextField(
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["fecha_vencimiento", "id"]
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

        constraints = [
            models.UniqueConstraint(
                models.F("medicamento"),
                Lower("numero"),
                name="lote_numero_unico_por_medicamento",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_actual__gte=0),
                name="lote_cantidad_no_negativa",
            ),
        ]

        indexes = [
            models.Index(
                fields=["medicamento", "fecha_vencimiento"],
                name="lote_med_venc_idx",
            ),
        ]

    def clean(self):
        super().clean()

        self.numero = (self.numero or "").strip()

        errores = {}

        if not self.numero:
            errores["numero"] = "Ingresá el número de lote."

        if (
            self.cantidad_actual is not None
            and self.cantidad_actual < 0
        ):
            errores["cantidad_actual"] = (
                "La cantidad disponible no puede ser negativa."
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if (
            self.fecha_vencimiento
            and self.fecha_vencimiento < timezone.localdate()
        ):
            self.activo = False

            # También persistimos la baja cuando el servicio
            # guarda únicamente stock y fecha de actualización.
            update_fields = kwargs.get("update_fields")

            if update_fields is not None:
                kwargs["update_fields"] = {
                    *update_fields,
                    "activo",
                }

        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.medicamento.nombre} — "
            f"Lote {self.numero}"
        )

class MovimientoStock(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        RETIRO = "RETIRO", "Retiro"
        AJUSTE_ENTRADA = "AJUSTE_ENTRADA", "Ajuste de entrada"
        AJUSTE_SALIDA = "AJUSTE_SALIDA", "Ajuste de salida"

    lote = models.ForeignKey(
        Lote,
        on_delete=models.PROTECT,
        related_name="movimientos",
    )

    tipo = models.CharField(
        max_length=14,
        choices=Tipo.choices,
    )

    cantidad = models.PositiveIntegerField(
        help_text="Cantidad de envases completos del movimiento.",
    )

    cantidad_anterior = models.PositiveIntegerField(
        editable=False,
    )

    cantidad_posterior = models.PositiveIntegerField(
        editable=False,
    )

    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimientos_stock",
        editable=False,
    )

    motivo = models.CharField(
        max_length=255,
    )

    observaciones = models.TextField(
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-fecha_creacion", "-id"]
        verbose_name = "Movimiento de stock"
        verbose_name_plural = "Movimientos de stock"

        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name="movimiento_cantidad_positiva",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        tipo__in=[
                            "INGRESO",
                            "AJUSTE_ENTRADA",
                        ],
                        cantidad_posterior=(
                            models.F("cantidad_anterior")
                            + models.F("cantidad")
                        ),
                    )
                    | models.Q(
                        tipo__in=[
                            "RETIRO",
                            "AJUSTE_SALIDA",
                        ],
                        cantidad_posterior=(
                            models.F("cantidad_anterior")
                            - models.F("cantidad")
                        ),
                    )
                ),
                name="movimiento_saldos_coherentes",
            ),
        ]

    def clean(self):
        super().clean()

        errores = {}

        self.motivo = (self.motivo or "").strip()

        if not self.motivo:
            errores["motivo"] = (
                "Ingresá el motivo del movimiento."
            )

        if self.cantidad is not None and self.cantidad <= 0:
            errores["cantidad"] = (
                "La cantidad debe ser mayor que cero."
            )

        tipos_entrada = {
            self.Tipo.INGRESO,
            self.Tipo.AJUSTE_ENTRADA,
        }

        tipos_salida = {
            self.Tipo.RETIRO,
            self.Tipo.AJUSTE_SALIDA,
        }

        if self.tipo not in tipos_entrada | tipos_salida:
            errores["tipo"] = (
                "Seleccioná un tipo de movimiento válido."
            )

        if (
            self.cantidad is not None
            and self.cantidad_anterior is not None
            and self.cantidad_posterior is not None
        ):
            if (
                self.cantidad_anterior < 0
                or self.cantidad_posterior < 0
            ):
                errores["cantidad"] = (
                    "Las existencias no pueden ser negativas."
                )

            if self.tipo in tipos_entrada:
                esperado = (
                    self.cantidad_anterior + self.cantidad
                )
            elif self.tipo in tipos_salida:
                esperado = (
                    self.cantidad_anterior - self.cantidad
                )
            else:
                esperado = None

            if (
                esperado is not None
                and self.cantidad_posterior != esperado
            ):
                errores["cantidad_posterior"] = (
                    "El saldo no coincide con el movimiento."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return (
            f"{self.get_tipo_display()} — "
            f"Lote {self.lote.numero} — "
            f"{self.cantidad} envases"
        )