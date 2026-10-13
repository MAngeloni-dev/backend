from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import Consulta


class ConsultaSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(
        source="paciente.nombre",
        read_only=True,
    )

    veterinario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "veterinario",
            "veterinario_nombre",
            "fecha",
            "motivo",
            "sintomas",
            "diagnostico",
            "tratamiento",
            "peso",
            "observaciones",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "veterinario",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_veterinario_nombre(self, obj):
        return (
            obj.veterinario.get_full_name()
            or obj.veterinario.username
        )

    def validate_fecha(self, value):
        if value > timezone.now():
            raise serializers.ValidationError(
                "La fecha de una consulta realizada no puede ser futura."
            )
        return value

    def validate(self, attrs):
        if self.instance:
            nuevo_paciente = attrs.get(
                "paciente",
                self.instance.paciente,
            )

            if nuevo_paciente.pk != self.instance.paciente_id:
                raise serializers.ValidationError({
                    "paciente": (
                        "No se puede cambiar el paciente de una consulta."
                    )
                })

        candidato = Consulta()

        if self.instance:
            for campo in Consulta._meta.concrete_fields:
                setattr(
                    candidato,
                    campo.attname,
                    getattr(self.instance, campo.attname),
                )

            candidato._state.adding = False

        for campo, valor in attrs.items():
            setattr(candidato, campo, valor)

        try:
            candidato.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict)

        return attrs