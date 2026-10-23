from copy import copy
from pacientes.models import Especie
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Lote, Medicamento, MovimientoStock


def validar_modelo(candidato):
    try:
        candidato.full_clean()
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


def preparar_candidato(instancia, modelo, attrs):
    if instancia is None:
        return modelo(**attrs)

    candidato = copy(instancia)
    candidato._state = copy(instancia._state)

    for campo, valor in attrs.items():
        setattr(candidato, campo, valor)

    return candidato


class MedicamentoSerializer(serializers.ModelSerializer):
    stock_utilizable = serializers.IntegerField(
    read_only=True,
    )
    class Meta:
        model = Medicamento
        fields = [
            "id",
            "nombre",
            "laboratorio",
            "principio_activo",
            "concentracion",
            "presentacion",
            "contenido_neto",
            "unidad_contenido",
            "codigo_barras",
            "via_administracion",
            "especies",
            "stock_minimo",
            "stock_minimo",
            "stock_utilizable",
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

    def validate(self, attrs):
        # La relación muchos a muchos se guarda después
        # de crear o actualizar el medicamento.
        datos_modelo = {
            campo: valor
            for campo, valor in attrs.items()
            if campo != "especies"
        }

        candidato = preparar_candidato(
            self.instance,
            Medicamento,
            datos_modelo,
        )

        validar_modelo(candidato)

        # Conservamos los valores normalizados por clean().
        for campo in datos_modelo:
            attrs[campo] = getattr(candidato, campo)

        if "especies" in attrs:
            if any(
                not especie.activo
                for especie in attrs["especies"]
            ):
                raise serializers.ValidationError(
                    {
                        "especies": [
                            "Seleccioná únicamente especies activas."
                        ]
                    }
                )

        return attrs


class LoteSerializer(serializers.ModelSerializer):
    medicamento_nombre = serializers.CharField(
        source="medicamento.nombre",
        read_only=True,
    )

    class Meta:
        model = Lote
        fields = [
            "id",
            "medicamento",
            "medicamento_nombre",
            "numero",
            "fecha_vencimiento",
            "cantidad_actual",
            "observaciones",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "cantidad_actual",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate(self, attrs):
        medicamento = attrs.get("medicamento")

        relacion_nueva = (
            self.instance is None
            or (
                medicamento is not None
                and medicamento.pk
                != self.instance.medicamento_id
            )
        )

        if (
            relacion_nueva
            and medicamento is not None
            and not medicamento.activo
        ):
            raise serializers.ValidationError(
                {
                    "medicamento": [
                        "Seleccioná un medicamento activo."
                    ]
                }
            )

        if (
            self.instance is not None
            and medicamento is not None
            and medicamento.pk
            != self.instance.medicamento_id
        ):
            raise serializers.ValidationError(
                {
                    "medicamento": [
                        "No se puede cambiar el medicamento "
                        "de un lote existente."
                    ]
                }
            )

        candidato = preparar_candidato(
            self.instance,
            Lote,
            attrs,
        )

        validar_modelo(candidato)

        for campo in list(attrs):
            attrs[campo] = getattr(candidato, campo)

        return attrs


class RegistrarMovimientoSerializer(serializers.Serializer):
    lote = serializers.IntegerField(
        min_value=1,
    )

    tipo = serializers.ChoiceField(
        choices=MovimientoStock.Tipo.choices,
    )

    cantidad = serializers.IntegerField(
        min_value=1,
        max_value=2147483647,
    )

    motivo = serializers.CharField(
        max_length=255,
        allow_blank=False,
        trim_whitespace=True,
    )

    observaciones = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class MovimientoStockSerializer(serializers.ModelSerializer):
    medicamento_nombre = serializers.CharField(
        source="lote.medicamento.nombre",
        read_only=True,
    )

    lote_numero = serializers.CharField(
        source="lote.numero",
        read_only=True,
    )

    responsable_nombre = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoStock
        fields = [
            "id",
            "lote",
            "lote_numero",
            "medicamento_nombre",
            "tipo",
            "cantidad",
            "cantidad_anterior",
            "cantidad_posterior",
            "responsable",
            "responsable_nombre",
            "motivo",
            "observaciones",
            "fecha_creacion",
        ]

        read_only_fields = fields

    def get_responsable_nombre(self, obj) -> str:
        return (
            obj.responsable.get_full_name().strip()
            or obj.responsable.username
        )

class EspecieResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especie
        fields = [
            "id",
            "nombre",
        ]


class MedicamentoResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicamento
        fields = [
            "id",
            "nombre",
            "concentracion",
            "presentacion",
        ]


class MedicamentoListadoSerializer(MedicamentoSerializer):
    especies_detalle = EspecieResumenSerializer(
        source="especies",
        many=True,
        read_only=True,
    )

    class Meta(MedicamentoSerializer.Meta):
        fields = [
            *MedicamentoSerializer.Meta.fields,
            "especies_detalle",
        ]


class LoteListadoSerializer(LoteSerializer):
    medicamento_detalle = MedicamentoResumenSerializer(
        source="medicamento",
        read_only=True,
    )

    class Meta(LoteSerializer.Meta):
        fields = [
            *LoteSerializer.Meta.fields,
            "medicamento_detalle",
        ]