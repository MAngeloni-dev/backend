from django import forms
from decimal import Decimal
from .models import Internacion
from pacientes.models import Paciente
from usuarios.models import Usuario


class AbrirInternacionAdminForm(forms.Form):
    paciente = forms.ModelChoiceField(
        queryset=Paciente.objects.filter(
            activo=True,
            tutor__activo=True,
        ).order_by("nombre"),
    )

    veterinario = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(
            is_active=True,
            rol__in=[
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.VETERINARIO,
            ],
        ).order_by("username"),
        label="Veterinario a cargo",
    )

    motivo = forms.CharField(
        max_length=255,
    )

    diagnostico = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label="Diagnóstico",
    )

    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )
class CerrarInternacionAdminForm(forms.Form):
    estado = forms.ChoiceField(
        label="Motivo del cierre",
        choices=[
            ("ALTA", "Alta"),
            ("FALLECIDO", "Fallecido"),
        ],
    )

class RegistrarEvolucionAdminForm(forms.Form):
    internacion = forms.ModelChoiceField(
        queryset=Internacion.objects.filter(
            estado=Internacion.Estado.INTERNADO,
        ).select_related("paciente"),
        label="Internación",
    )

    observaciones = forms.CharField(
        widget=forms.Textarea,
    )

    indicaciones = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    peso = forms.DecimalField(
        label="Peso en kg",
        max_digits=7,
        decimal_places=3,
        min_value=Decimal("0.001"),
        required=False,
    )

    temperatura = forms.DecimalField(
        label="Temperatura en °C",
        max_digits=4,
        decimal_places=1,
        required=False,
    )

    frecuencia_cardiaca = forms.IntegerField(
        label="Frecuencia cardíaca",
        min_value=1,
        max_value=2147483647,
        required=False,
        help_text="Latidos por minuto.",
    )

    frecuencia_respiratoria = forms.IntegerField(
        label="Frecuencia respiratoria",
        min_value=1,
        max_value=2147483647,
        required=False,
        help_text="Respiraciones por minuto.",
    )