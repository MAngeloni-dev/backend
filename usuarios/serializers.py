from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


Usuario = get_user_model()


class ProfesionalSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "nombre"]
        read_only_fields = fields

    def get_nombre(self, obj) -> str:
        return obj.get_full_name().strip() or obj.username


class UsuarioActualSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "rol",
            "foto",
        ]
        read_only_fields = fields


class ActualizarPerfilSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=150,
        allow_blank=False,
        trim_whitespace=True,
    )
    last_name = serializers.CharField(
        max_length=150,
        allow_blank=False,
        trim_whitespace=True,
    )
    foto = serializers.ImageField(required=False)

    class Meta:
        model = Usuario
        fields = [
            "first_name",
            "last_name",
            "foto",
        ]

    def validate_foto(self, archivo):
        if archivo.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "La foto no puede superar los 5 MB."
            )

        imagen = archivo.image

        if imagen.format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError(
                "Seleccioná una imagen JPG, PNG o WebP."
            )

        ancho, alto = imagen.size

        if ancho > 4096 or alto > 4096:
            raise serializers.ValidationError(
                "La imagen no puede superar los 4096 píxeles "
                "de ancho o alto."
            )

        return archivo


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=1024,
        style={"input_type": "password"},
    )
    password_nueva = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
        style={"input_type": "password"},
    )
    password_confirmacion = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        usuario = self.context["request"].user

        if not usuario.check_password(attrs["password_actual"]):
            raise serializers.ValidationError(
                {
                    "password_actual": [
                        "La contraseña actual no es correcta."
                    ]
                }
            )

        nueva = attrs["password_nueva"]

        if nueva != attrs["password_confirmacion"]:
            raise serializers.ValidationError(
                {
                    "password_confirmacion": [
                        "Las contraseñas no coinciden."
                    ]
                }
            )

        if usuario.check_password(nueva):
            raise serializers.ValidationError(
                {
                    "password_nueva": [
                        "La nueva contraseña debe ser diferente "
                        "de la actual."
                    ]
                }
            )

        try:
            validate_password(nueva, user=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"password_nueva": error.messages}
            ) from error

        return attrs