from pathlib import Path
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models


def ruta_foto_perfil(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"perfiles/{uuid4().hex}{extension}"


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        VETERINARIO = "VETERINARIO", "Veterinario"
        RECEPCION = "RECEPCION", "Recepción"

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.RECEPCION,
    )

    foto = models.ImageField(
        upload_to=ruta_foto_perfil,
        blank=True,
    )

    def __str__(self):
        return self.get_full_name() or self.username