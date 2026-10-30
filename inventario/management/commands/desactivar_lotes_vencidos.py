from django.core.management.base import BaseCommand
from django.utils import timezone

from inventario.models import Lote


class Command(BaseCommand):
    help = "Desactiva lotes vencidos sin modificar sus existencias."

    def handle(self, *args, **options):
        ahora = timezone.now()

        cantidad = Lote.objects.filter(
            activo=True,
            fecha_vencimiento__lt=timezone.localdate(ahora),
        ).update(
            activo=False,
            fecha_actualizacion=ahora,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Lotes desactivados: {cantidad}."
            )
        )