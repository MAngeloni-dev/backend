from contextlib import contextmanager
from datetime import timedelta
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import F, Q, Sum
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from .models import Lote, Medicamento, MovimientoStock
from .permissions import PuedeGestionarInventario
from .serializers import (
    LoteSerializer,
    MedicamentoSerializer,
    MovimientoStockSerializer,
    RegistrarMovimientoSerializer,
    MedicamentoListadoSerializer,
    LoteListadoSerializer,
)
from .services import registrar_movimiento


@contextmanager
def controlar_duplicados():
    try:
        with transaction.atomic():
            yield
    except IntegrityError as error:
        codigo = getattr(error.__cause__, "sqlstate", None)

        if codigo == "23505":
            raise ValidationError(
                {
                    "detail": (
                        "Ya existe un registro con esos datos únicos. "
                        "Revisá el código de barras, la presentación "
                        "del medicamento o el número de lote."
                    )
                }
            ) from error

        raise


class GestionCatalogoViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        PuedeGestionarInventario,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    def perform_create(self, serializer):
        with controlar_duplicados():
            serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        with controlar_duplicados():
            self.queryset = self.get_queryset().select_for_update(
                of=("self",)
            )

            instancia = self.get_object()

            serializer = self.get_serializer(
                instancia,
                data=request.data,
                partial=partial,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            datos = serializer.data

        return Response(datos)

    def destroy(self, request, *args, **kwargs):
        # La baja es lógica: conservamos relaciones e historial.
        with transaction.atomic():
            self.queryset = self.get_queryset().select_for_update(
                of=("self",)
            )

            instancia = self.get_object()
            instancia.activo = False
            instancia.save(
                update_fields=[
                    "activo",
                    "fecha_actualizacion",
                ]
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MedicamentoViewSet(GestionCatalogoViewSet):
    def get_serializer_class(self):
        if self.action == "list":
            return MedicamentoListadoSerializer

        return MedicamentoSerializer
    queryset = Medicamento.objects.prefetch_related(
        "especies"
    ).all()

    serializer_class = MedicamentoSerializer

    filterset_fields = [
        "activo",
        "especies",
        "via_administracion",
    ]

    search_fields = [
        "nombre",
        "laboratorio",
        "principio_activo",
        "codigo_barras",
    ]

    ordering_fields = [
        "nombre",
        "stock_minimo",
        "fecha_creacion",
    ]

    ordering = ["nombre", "id"]

    def get_queryset(self):
        hoy = timezone.localdate()

        return super().get_queryset().annotate(
            stock_utilizable=Sum(
                "lotes__cantidad_actual",
                filter=Q(
                    lotes__activo=True,
                    lotes__fecha_vencimiento__gte=hoy,
                ),
                default=0,
            )
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="stock-bajo",
    )
    def stock_bajo(self, request):
        queryset = self.filter_queryset(
            self.get_queryset()
        ).filter(
            activo=True,
            stock_utilizable__lte=F("stock_minimo"),
        ).distinct()

        pagina = self.paginate_queryset(queryset)

        if pagina is not None:
            serializer = self.get_serializer(
                pagina,
                many=True,
            )
            return self.get_paginated_response(
                serializer.data
            )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)


class LoteViewSet(GestionCatalogoViewSet):
    queryset = Lote.objects.select_related(
        "medicamento"
    ).all()

    serializer_class = LoteSerializer

    filterset_fields = {
        "medicamento": ["exact"],
        "activo": ["exact"],
        "fecha_vencimiento": ["gte", "lte", "lt"],
    }

    search_fields = [
        "numero",
        "medicamento__nombre",
        "medicamento__codigo_barras",
    ]

    ordering_fields = [
        "fecha_vencimiento",
        "cantidad_actual",
        "fecha_creacion",
    ]

    ordering = ["fecha_vencimiento", "id"]

    def get_serializer_class(self):
        if self.action == "list":
            return LoteListadoSerializer

        return LoteSerializer

    def responder_listado(self, queryset):
        queryset = self.filter_queryset(queryset)
        pagina = self.paginate_queryset(queryset)

        if pagina is not None:
            serializer = self.get_serializer(
                pagina,
                many=True,
            )
            return self.get_paginated_response(
                serializer.data
            )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="proximos-vencer",
    )
    def proximos_vencer(self, request):
        try:
            dias = int(
                request.query_params.get("dias", "30")
            )
        except (TypeError, ValueError):
            raise ValidationError(
                {
                    "dias": [
                        "Ingresá un número entero entre 1 y 365."
                    ]
                }
            )

        if not 1 <= dias <= 365:
            raise ValidationError(
                {
                    "dias": [
                        "Ingresá un número entero entre 1 y 365."
                    ]
                }
            )

        hoy = timezone.localdate()
        fecha_limite = hoy + timedelta(days=dias)

        queryset = self.get_queryset().filter(
            activo=True,
            medicamento__activo=True,
            cantidad_actual__gt=0,
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=fecha_limite,
        )

        return self.responder_listado(queryset)

    @action(
        detail=False,
        methods=["get"],
        url_path="vencidos",
    )
    def vencidos(self, request):
        queryset = self.get_queryset().filter(
            cantidad_actual__gt=0,
            fecha_vencimiento__lt=timezone.localdate(),
        )

        return self.responder_listado(queryset)


class MovimientoStockViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = MovimientoStock.objects.select_related(
        "lote",
        "lote__medicamento",
        "responsable",
    ).all()

    permission_classes = [
        IsAuthenticated,
        PuedeGestionarInventario,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = {
        "lote": ["exact"],
        "lote__medicamento": ["exact"],
        "tipo": ["exact"],
        "responsable": ["exact"],
        "fecha_creacion": ["gte", "lt"],
    }

    search_fields = [
        "lote__numero",
        "lote__medicamento__nombre",
        "motivo",
        "observaciones",
    ]

    ordering_fields = [
        "fecha_creacion",
        "cantidad",
    ]

    ordering = ["-fecha_creacion", "-id"]

    def get_serializer_class(self):
        if self.action == "create":
            return RegistrarMovimientoSerializer

        return MovimientoStockSerializer
    
    @extend_schema(
        summary="Registrar un movimiento de stock",
        description=(
            "Registra un ingreso, retiro o ajuste y actualiza "
            "las existencias del lote en una transacción. "
            "Solo administrador y veterinario pueden realizarlo."
        ),
        request=RegistrarMovimientoSerializer,
        responses={
            201: MovimientoStockSerializer,
        },
    )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data

        movimiento = registrar_movimiento(
            lote_id=datos["lote"],
            tipo=datos["tipo"],
            cantidad=datos["cantidad"],
            motivo=datos["motivo"],
            observaciones=datos["observaciones"],
            responsable=request.user,
        )

        respuesta = MovimientoStockSerializer(
            movimiento,
            context=self.get_serializer_context(),
        )

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED,
        )