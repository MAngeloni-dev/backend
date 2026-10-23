from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EvolucionInternacion, Internacion
from .permissions import PuedeGestionarInternaciones
from .serializers import (
    AbrirInternacionSerializer,
    CerrarInternacionSerializer,
    EvolucionInternacionSerializer,
    InternacionSerializer,
    RegistrarEvolucionSerializer,
)
from .services import (
    abrir_internacion,
    cerrar_internacion,
    registrar_evolucion,
)


class InternacionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Internacion.objects.select_related(
        "paciente",
        "veterinario",
        "creado_por",
    ).all()

    permission_classes = [
        IsAuthenticated,
        PuedeGestionarInternaciones,
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
        "fecha_ingreso": ["gte", "lt"],
    }

    search_fields = [
        "paciente__nombre",
        "motivo",
        "diagnostico",
    ]

    ordering_fields = [
        "fecha_ingreso",
        "fecha_egreso",
        "fecha_creacion",
    ]

    ordering = ["-fecha_ingreso", "-id"]

    def get_serializer_class(self):
        if self.action == "create":
            return AbrirInternacionSerializer

        if self.action == "cerrar":
            return CerrarInternacionSerializer

        return InternacionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data

        internacion = abrir_internacion(
            paciente_id=datos["paciente"],
            veterinario_id=datos["veterinario"],
            motivo=datos["motivo"],
            responsable=request.user,
            fecha_ingreso=datos.get("fecha_ingreso"),
            diagnostico=datos["diagnostico"],
            observaciones=datos["observaciones"],
        )

        respuesta = InternacionSerializer(
            internacion,
            context=self.get_serializer_context(),
        )

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        # Verifica que el registro exista y sea accesible.
        internacion = self.get_object()

        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data

        internacion = cerrar_internacion(
            internacion_id=internacion.pk,
            estado=datos["estado"],
            responsable=request.user,
            fecha_egreso=datos.get("fecha_egreso"),
        )

        respuesta = InternacionSerializer(
            internacion,
            context=self.get_serializer_context(),
        )

        return Response(respuesta.data)


class EvolucionInternacionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = EvolucionInternacion.objects.select_related(
        "internacion",
        "profesional",
    ).all()

    permission_classes = [
        IsAuthenticated,
        PuedeGestionarInternaciones,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = {
        "internacion": ["exact"],
        "internacion__paciente": ["exact"],
        "profesional": ["exact"],
        "fecha": ["gte", "lt"],
    }

    search_fields = [
        "internacion__paciente__nombre",
        "observaciones",
        "indicaciones",
    ]

    ordering_fields = [
        "fecha",
        "fecha_creacion",
    ]

    ordering = ["-fecha", "-id"]

    def get_serializer_class(self):
        if self.action == "create":
            return RegistrarEvolucionSerializer

        return EvolucionInternacionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data

        evolucion = registrar_evolucion(
            internacion_id=datos["internacion"],
            responsable=request.user,
            observaciones=datos["observaciones"],
            fecha=datos.get("fecha"),
            indicaciones=datos["indicaciones"],
            peso=datos.get("peso"),
            temperatura=datos.get("temperatura"),
            frecuencia_cardiaca=datos.get(
                "frecuencia_cardiaca"
            ),
            frecuencia_respiratoria=datos.get(
                "frecuencia_respiratoria"
            ),
        )

        respuesta = EvolucionInternacionSerializer(
            evolucion,
            context=self.get_serializer_context(),
        )

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED,
        )