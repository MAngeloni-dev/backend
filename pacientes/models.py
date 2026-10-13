from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Tutor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField("DNI", max_length=20, blank=True)
    telefono = models.CharField("Teléfono", max_length=30)
    email = models.EmailField(blank=True)
    direccion = models.CharField("Dirección", max_length=255, blank=True)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellido", "nombre"]
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class Especie(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                name="especie_nombre_unico",
            )
        ]

    def __str__(self):
        return self.nombre


class Raza(models.Model):
    nombre = models.CharField(max_length=100)
    especie = models.ForeignKey(
        Especie,
        on_delete=models.PROTECT,
        related_name="razas",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["especie__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                "especie",
                name="raza_nombre_unico_por_especie",
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.especie.nombre})"


class Paciente(models.Model):
    class Sexo(models.TextChoices):
        MACHO = "MACHO", "Macho"
        HEMBRA = "HEMBRA", "Hembra"
        DESCONOCIDO = "DESCONOCIDO", "Desconocido"

    class Castracion(models.TextChoices):
        SI = "SI", "Sí"
        NO = "NO", "No"
        DESCONOCIDO = "DESCONOCIDO", "Desconocido"

    nombre = models.CharField(max_length=100)

    tutor = models.ForeignKey(
        Tutor,
        on_delete=models.PROTECT,
        related_name="pacientes",
    )
    especie = models.ForeignKey(
        Especie,
        on_delete=models.PROTECT,
        related_name="pacientes",
    )
    raza = models.ForeignKey(
        Raza,
        on_delete=models.PROTECT,
        related_name="pacientes",
        blank=True,
        null=True,
    )

    sexo = models.CharField(
        max_length=12,
        choices=Sexo.choices,
        default=Sexo.DESCONOCIDO,
    )
    fecha_nacimiento = models.DateField(blank=True, null=True)
    nacimiento_estimado = models.BooleanField(default=False)

    castrado = models.CharField(
        max_length=12,
        choices=Castracion.choices,
        default=Castracion.DESCONOCIDO,
    )

    color = models.CharField(max_length=100, blank=True)
    microchip = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"

    def clean(self):
        super().clean()
        errores = {}

        self.microchip = (self.microchip or "").strip() or None

        if self.fecha_nacimiento:
            if self.fecha_nacimiento > timezone.localdate():
                errores["fecha_nacimiento"] = (
                    "La fecha de nacimiento no puede ser futura."
                )
        elif self.nacimiento_estimado:
            errores["nacimiento_estimado"] = (
                "Indicá una fecha de nacimiento estimada."
            )

        if self.raza_id and self.especie_id:
            especie_raza = (
                Raza.objects.filter(pk=self.raza_id)
                .values_list("especie_id", flat=True)
                .first()
            )
            if especie_raza is not None and especie_raza != self.especie_id:
                errores["raza"] = (
                    "La raza seleccionada no pertenece a la especie."
                )

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.nombre} — {self.tutor}"