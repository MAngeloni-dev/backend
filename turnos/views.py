from contextlib import contextmanager

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    filters,
    mixins,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Turno
from .permissions import PuedeGestionarTurnos
from .serializers import TurnoSerializer


@contextmanager
def controlar_conflictos():
    try:
        with transaction.atomic():
            yield
    except IntegrityError as error:
        diagnostico = getattr(error.__cause__, "diag", None)
        restriccion = getattr(
            diagnostico,
            "constraint_name",
            None,
        )

        if restriccion == "turno_sin_superposicion_profesional":
            raise serializers.ValidationError(
                {
                    "inicio": [
                        "El profesional ya tiene un turno en ese horario."
                    ]
                }
            ) from error

        if restriccion == "turno_fin_posterior_inicio":
            raise serializers.ValidationError(
                {
                    "fin": [
                        "La hora de finalización debe ser posterior al inicio."
                    ]
                }
            ) from error

        raise


class TurnoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Turno.objects.select_related(
        "paciente",
        "paciente__tutor",
        "veterinario",
        "creado_por",
    ).all()

    serializer_class = TurnoSerializer

    permission_classes = [
        IsAuthenticated,
        PuedeGestionarTurnos,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = {
        "paciente": ["exact"],
        "veterinario": ["exact"],
        "estado": ["exact"],
        "inicio": ["gte", "lt"],
        "fin": ["gt", "lte"],
    }

    search_fields = [
        "paciente__nombre",
        "paciente__tutor__nombre",
        "paciente__tutor__apellido",
        "motivo",
    ]

    ordering_fields = [
        "inicio",
        "fin",
        "fecha_creacion",
    ]

    ordering = ["inicio", "id"]

    def perform_create(self, serializer):
        with controlar_conflictos():
            serializer.save(
                creado_por=self.request.user,
                estado=Turno.Estado.PENDIENTE,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        with controlar_conflictos():
            # Bloqueamos el turno durante la edición para evitar
            # conflictos con otra edición o cambio de estado.
            self.queryset = self.get_queryset().select_for_update(
                of=("self",)
            )

            turno = self.get_object()

            if turno.estado in {
                Turno.Estado.CANCELADO,
                Turno.Estado.ATENDIDO,
            }:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "Solo se pueden editar turnos pendientes "
                            "o confirmados."
                        )
                    }
                )

            serializer = self.get_serializer(
                turno,
                data=request.data,
                partial=partial,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            datos = serializer.data

        return Response(datos)

    def cambiar_estado(self, estado_destino, estados_permitidos):
        with controlar_conflictos():
            self.queryset = self.get_queryset().select_for_update(
                of=("self",)
            )

            turno = self.get_object()

            if turno.estado not in estados_permitidos:
                raise serializers.ValidationError(
                    {
                        "estado": [
                            "El estado actual del turno no permite "
                            "realizar esta operación."
                        ]
                    }
                )

            turno.estado = estado_destino

            try:
                turno.clean()
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

            turno.save(
                update_fields=[
                    "estado",
                    "fecha_actualizacion",
                ]
            )

            datos = self.get_serializer(turno).data

        return Response(
            datos,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        return self.cambiar_estado(
            estado_destino=Turno.Estado.CONFIRMADO,
            estados_permitidos={
                Turno.Estado.PENDIENTE,
            },
        )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        return self.cambiar_estado(
            estado_destino=Turno.Estado.CANCELADO,
            estados_permitidos={
                Turno.Estado.PENDIENTE,
                Turno.Estado.CONFIRMADO,
            },
        )

    @action(detail=True, methods=["post"])
    def atender(self, request, pk=None):
        return self.cambiar_estado(
            estado_destino=Turno.Estado.ATENDIDO,
            estados_permitidos={
                Turno.Estado.PENDIENTE,
                Turno.Estado.CONFIRMADO,
            },
        )