from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from pacientes.views import PaginacionCRM

from .models import Consulta
from .permissions import PuedeGestionarConsultas
from .serializers import ConsultaSerializer


class ConsultaViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Consulta.objects.select_related(
        "paciente",
        "veterinario",
    ).all()

    serializer_class = ConsultaSerializer
    pagination_class = PaginacionCRM

    permission_classes = [
        permissions.IsAuthenticated,
        PuedeGestionarConsultas,
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = ["paciente", "veterinario"]
    search_fields = [
        "paciente__nombre",
        "motivo",
        "diagnostico",
    ]
    ordering_fields = ["fecha", "fecha_creacion"]
    ordering = ["-fecha", "-id"]

    def perform_create(self, serializer):
        serializer.save(veterinario=self.request.user)