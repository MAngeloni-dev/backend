from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    ProfesionalSerializer,
    UsuarioActualSerializer,
)


Usuario = get_user_model()


class UsuarioActualView(RetrieveAPIView):
    serializer_class = UsuarioActualSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfesionalListView(ListAPIView):
    serializer_class = ProfesionalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Usuario.objects.filter(
                is_active=True,
                rol__in=[
                    Usuario.Rol.ADMINISTRADOR,
                    Usuario.Rol.VETERINARIO,
                ],
            )
            .only("id", "username", "first_name", "last_name")
            .order_by("first_name", "last_name", "username", "id")
        )