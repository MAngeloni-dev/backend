from rest_framework import serializers

from .models import Usuario


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