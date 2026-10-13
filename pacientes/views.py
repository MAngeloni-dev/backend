from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Especie, Paciente, Raza, Tutor
from .serializers import (
    EspecieSerializer,
    PacienteSerializer,
    RazaSerializer,
    TutorSerializer,
)
from usuarios.permissions import PuedeGestionarTutoresPacientes


class PaginacionCRM(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer
    permission_classes = [permissions.IsAuthenticated, PuedeGestionarTutoresPacientes]
    pagination_class = PaginacionCRM

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    filterset_fields = ["activo"]
    search_fields = [
        "nombre",
        "apellido",
        "dni",
        "telefono",
        "email",
    ]
    ordering_fields = ["nombre", "apellido", "fecha_creacion"]
    ordering = ["apellido", "nombre"]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(update_fields=["activo", "fecha_actualizacion"])


class EspecieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Especie.objects.filter(activo=True)
    serializer_class = EspecieSerializer
    permission_classes = [permissions.IsAuthenticated]


class RazaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Raza.objects.filter(
            activo=True,
            especie__activo=True,
        )
        .select_related("especie")
        .order_by("nombre")
    )
    serializer_class = RazaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["especie"]

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.select_related(
        "tutor",
        "especie",
        "raza",
        "raza__especie",
    ).all()

    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated, PuedeGestionarTutoresPacientes]
    pagination_class = PaginacionCRM

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "activo",
        "tutor",
        "especie",
        "raza",
        "sexo",
    ]

    search_fields = [
        "nombre",
        "microchip",
        "tutor__nombre",
        "tutor__apellido",
    ]

    ordering_fields = [
        "nombre",
        "fecha_nacimiento",
        "fecha_creacion",
    ]
    ordering = ["nombre"]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save(
            update_fields=["activo", "fecha_actualizacion"]
        )