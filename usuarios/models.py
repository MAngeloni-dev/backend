from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def __str__(self):
        return self.get_full_name() or self.username