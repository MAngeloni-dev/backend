from rest_framework import serializers

from .models import Usuario

from django.contrib.auth import get_user_model

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
        ]
        read_only_fields = fields