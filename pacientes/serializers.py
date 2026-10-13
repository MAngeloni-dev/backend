from rest_framework import serializers

from .models import Especie, Paciente, Raza, Tutor
from django.core.exceptions import ValidationError as DjangoValidationError


class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        fields = [
            "id",
            "nombre",
            "apellido",
            "dni",
            "telefono",
            "email",
            "direccion",
            "observaciones",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

class EspecieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especie
        fields = ["id", "nombre", "activo"]
        read_only_fields = ["id"]


class RazaSerializer(serializers.ModelSerializer):
    especie_nombre = serializers.CharField(
        source="especie.nombre",
        read_only=True,
    )

    class Meta:
        model = Raza
        fields = [
            "id",
            "nombre",
            "especie",
            "especie_nombre",
            "activo",
        ]
        read_only_fields = ["id"]

class PacienteSerializer(serializers.ModelSerializer):
    tutor_detalle = TutorSerializer(
        source="tutor",
        read_only=True,
    )
    especie_detalle = EspecieSerializer(
        source="especie",
        read_only=True,
    )
    raza_detalle = RazaSerializer(
        source="raza",
        read_only=True,
    )

    class Meta:
        model = Paciente
        fields = [
            "id",
            "nombre",
            "tutor",
            "tutor_detalle",
            "especie",
            "especie_detalle",
            "raza",
            "raza_detalle",
            "sexo",
            "fecha_nacimiento",
            "nacimiento_estimado",
            "castrado",
            "color",
            "microchip",
            "observaciones",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_microchip(self, value):
        return (value or "").strip() or None

    def validate(self, attrs):
        # Combinar los datos actuales con los recibidos permite
        # validar también actualizaciones parciales con PATCH.
        valores = {}

        if self.instance:
            for campo in Paciente._meta.concrete_fields:
                valores[campo.attname] = getattr(
                    self.instance,
                    campo.attname,
                )

        candidato = Paciente(**valores)

        for campo, valor in attrs.items():
            setattr(candidato, campo, valor)

        errores = {}

        # Exigir relaciones activas al crear o cambiar su selección.
        # Una relación histórica desactivada puede conservarse.
        for campo in ("tutor", "especie", "raza"):
            relacion = getattr(candidato, campo)

            if relacion is None:
                continue

            id_anterior = (
                getattr(self.instance, f"{campo}_id")
                if self.instance
                else None
            )

            if relacion.pk != id_anterior and not relacion.activo:
                errores[campo] = (
                    "Seleccioná un registro activo."
                )

        try:
            candidato.clean()
        except DjangoValidationError as error:
            errores.update(error.message_dict)

        if errores:
            raise serializers.ValidationError(errores)

        return attrs