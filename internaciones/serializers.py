from decimal import Decimal

from rest_framework import serializers

from .models import EvolucionInternacion, Internacion


class AbrirInternacionSerializer(serializers.Serializer):
    paciente = serializers.IntegerField(
        min_value=1,
    )

    veterinario = serializers.IntegerField(
        min_value=1,
    )

    motivo = serializers.CharField(
        max_length=255,
        allow_blank=False,
        trim_whitespace=True,
    )

    fecha_ingreso = serializers.DateTimeField(
        required=False,
    )

    diagnostico = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class CerrarInternacionSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=[
            (
                Internacion.Estado.ALTA,
                "Alta",
            ),
            (
                Internacion.Estado.FALLECIDO,
                "Fallecido",
            ),
        ],
    )

    fecha_egreso = serializers.DateTimeField(
        required=False,
    )


class RegistrarEvolucionSerializer(serializers.Serializer):
    internacion = serializers.IntegerField(
        min_value=1,
    )

    fecha = serializers.DateTimeField(
        required=False,
    )

    observaciones = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    indicaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    peso = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
        allow_null=True,
    )

    temperatura = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        required=False,
        allow_null=True,
    )

    frecuencia_cardiaca = serializers.IntegerField(
        min_value=1,
        max_value=2147483647,
        required=False,
        allow_null=True,
    )

    frecuencia_respiratoria = serializers.IntegerField(
        min_value=1,
        max_value=2147483647,
        required=False,
        allow_null=True,
    )


class InternacionSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.CharField(
        source="paciente.nombre",
        read_only=True,
    )

    veterinario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Internacion
        fields = [
            "id",
            "paciente",
            "paciente_nombre",
            "veterinario",
            "veterinario_nombre",
            "fecha_ingreso",
            "fecha_egreso",
            "motivo",
            "diagnostico",
            "observaciones",
            "estado",
            "creado_por",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = fields

    def get_veterinario_nombre(self, obj) -> str:
        return (
            obj.veterinario.get_full_name().strip()
            or obj.veterinario.username
        )


class EvolucionInternacionSerializer(
    serializers.ModelSerializer
):
    profesional_nombre = serializers.SerializerMethodField()

    class Meta:
        model = EvolucionInternacion
        fields = [
            "id",
            "internacion",
            "profesional",
            "profesional_nombre",
            "fecha",
            "peso",
            "temperatura",
            "frecuencia_cardiaca",
            "frecuencia_respiratoria",
            "observaciones",
            "indicaciones",
            "fecha_creacion",
        ]
        read_only_fields = fields

    def get_profesional_nombre(self, obj) -> str:
        return (
            obj.profesional.get_full_name().strip()
            or obj.profesional.username
        )