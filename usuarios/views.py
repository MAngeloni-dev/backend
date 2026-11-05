from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    ActualizarPerfilSerializer,
    CambiarPasswordSerializer,
    ProfesionalSerializer,
    UsuarioActualSerializer,
)


Usuario = get_user_model()


class MensajeSerializer(serializers.Serializer):
    detail = serializers.CharField(read_only=True)


class UsuarioActualView(RetrieveAPIView):
    serializer_class = UsuarioActualSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ActualizarPerfilView(GenericAPIView):
    serializer_class = ActualizarPerfilSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    @extend_schema(
        summary="Actualizar mi perfil",
        responses=UsuarioActualSerializer,
    )
    def patch(self, request, *args, **kwargs):
        with transaction.atomic():
            usuario = (
                Usuario.objects.select_for_update()
                .get(pk=request.user.pk)
            )

            serializer = self.get_serializer(
                usuario,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(
            UsuarioActualSerializer(
                usuario,
                context=self.get_serializer_context(),
            ).data
        )


class CambiarPasswordView(GenericAPIView):
    serializer_class = CambiarPasswordSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cambiar mi contraseña",
        responses={200: MensajeSerializer},
    )
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            usuario = (
                Usuario.objects.select_for_update()
                .get(pk=request.user.pk)
            )

            # Validamos contra la cuenta recién leída y bloqueada.
            request.user = usuario

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            usuario.set_password(
                serializer.validated_data["password_nueva"]
            )
            usuario.save(update_fields=["password"])

        return Response(
            {
                "detail": (
                    "Contraseña actualizada. "
                    "Iniciá sesión nuevamente."
                )
            },
            status=status.HTTP_200_OK,
        )


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
            .order_by(
                "first_name",
                "last_name",
                "username",
                "id",
            )
        )