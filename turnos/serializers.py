from copy import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Turno


class TurnoSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(
        source="paciente.nombre",
        read_only=True,
    )
    veterinario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Turno
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "veterinario",
            "veterinario_nombre",
            "inicio",
            "fin",
            "motivo",
            "observaciones",
            "estado",
            "creado_por",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "estado",
            "creado_por",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_veterinario_nombre(self, obj) -> str:
        return (
            obj.veterinario.get_full_name().strip()
            or obj.veterinario.username
        )

    def validate_motivo(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Ingresá el motivo del turno."
            )

        return value

    def validate(self, attrs):
        # En una edición combinamos los valores actuales
        # con los recibidos, sin modificar la instancia original.
        if self.instance is not None:
            candidato = copy(self.instance)
            candidato._state = copy(self.instance._state)

            for campo, valor in attrs.items():
                setattr(candidato, campo, valor)
        else:
            candidato = Turno(**attrs)

        try:
            candidato.clean()
        except DjangoValidationError as error:
            if hasattr(error, "message_dict"):
                detalle = {
                    (
                        "non_field_errors"
                        if campo == "__all__"
                        else campo
                    ): mensajes
                    for campo, mensajes in error.message_dict.items()
                }
            else:
                detalle = {
                    "non_field_errors": error.messages,
                }

            raise serializers.ValidationError(detalle) from error

        return attrs