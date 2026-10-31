from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pacientes.models import Especie, Raza


# Nombre preferido, nombres equivalentes y razas.
# Las especies sin razas pueden usarse con raza sin registrar.
CATALOGO = [
    (
        "Perro",
        ["Canino", "Canina", "Perros"],
        [
            "Mestizo",
            "Labrador Retriever",
            "Golden Retriever",
            "Pastor alemán",
            "Caniche",
            "Beagle",
            "Bulldog francés",
            "Bulldog inglés",
            "Chihuahua",
            "Dachshund",
            "Boxer",
            "Rottweiler",
            "Doberman",
            "Dálmata",
            "Border Collie",
            "Cocker Spaniel inglés",
            "Shih Tzu",
            "Yorkshire Terrier",
            "Pug",
            "Schnauzer miniatura",
            "Husky siberiano",
            "Dogo argentino",
            "Bichón frisé",
            "Maltés",
            "Pomerania",
        ],
    ),
    (
        "Gato",
        ["Felino", "Felina", "Gatos"],
        [
            "Mestizo",
            "Común europeo",
            "Siamés",
            "Persa",
            "Maine Coon",
            "Ragdoll",
            "Bengalí",
            "Sphynx",
            "British Shorthair",
            "Azul ruso",
            "Abisinio",
            "Bosque de Noruega",
            "Exótico de pelo corto",
            "Angora turco",
        ],
    ),
    (
        "Conejo",
        ["Conejos", "Conejo doméstico"],
        [
            "Mestizo",
            "Rex",
            "Mini Rex",
            "Cabeza de León",
            "Neerlandés enano",
            "Belier francés",
            "Belier inglés",
            "Holland Lop",
            "Mini Lop",
            "Californiano",
            "Nueva Zelanda",
            "Gigante de Flandes",
            "Angora inglés",
            "Holandés",
        ],
    ),
    (
        "Cobayo",
        ["Cobaya", "Cuy", "Cobayos", "Cavia porcellus"],
        [
            "Americano",
            "Abisinio",
            "Peruano",
            "Silkie",
            "Coronet",
            "Texel",
            "Teddy",
            "Rex",
            "Skinny",
            "Baldwin",
        ],
    ),
    ("Chinchilla", ["Chinchilla doméstica"], []),
    ("Hurón", ["Hurón doméstico"], []),
    ("Hámster sirio", ["Hámster dorado"], []),
    ("Hámster enano ruso", [], []),
    ("Hámster de Roborovski", [], []),
    ("Rata doméstica", [], []),
    ("Ratón doméstico", [], []),
    ("Jerbo de Mongolia", [], []),
    ("Degú", [], []),
    ("Erizo africano", [], []),
    ("Periquito australiano", [], []),
    ("Canario", [], []),
    ("Ninfa", ["Carolina"], []),
    ("Agapornis roseicollis", [], []),
    ("Diamante mandarín", [], []),
    ("Gecko leopardo", [], []),
    ("Gecko crestado", [], []),
    ("Dragón barbudo", ["Pogona vitticeps"], []),
    ("Serpiente del maíz", [], []),
    ("Pitón real", [], []),
]


class Command(BaseCommand):
    help = (
        "Carga especies y razas de animales de compañía "
        "sin duplicar nombres ni modificar registros existentes."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        especies_creadas = 0
        razas_creadas = 0

        for nombre, equivalentes, razas in CATALOGO:
            coincidencias = Especie.objects.none()

            for candidato in [nombre, *equivalentes]:
                coincidencias = (
                    coincidencias
                    | Especie.objects.filter(
                        nombre__iexact=candidato
                    )
                )

            existentes = list(
                coincidencias.distinct().order_by("id")
            )

            if len(existentes) > 1:
                nombres = ", ".join(
                    f"{item.nombre} (#{item.pk})"
                    for item in existentes
                )
                raise CommandError(
                    f"Hay especies equivalentes: {nombres}. "
                    "Revisalas antes de continuar. "
                    "Se canceló la carga completa."
                )

            if existentes:
                especie = existentes[0]
            else:
                especie = Especie.objects.create(
                    nombre=nombre,
                    activo=True,
                )
                especies_creadas += 1

            for nombre_raza in razas:
                existe = Raza.objects.filter(
                    especie=especie,
                    nombre__iexact=nombre_raza,
                ).exists()

                if not existe:
                    Raza.objects.create(
                        especie=especie,
                        nombre=nombre_raza,
                        activo=True,
                    )
                    razas_creadas += 1

            self.stdout.write(
                f"Catálogo revisado: {especie.nombre}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Especies creadas: {especies_creadas}. "
                f"Razas creadas: {razas_creadas}."
            )
        )