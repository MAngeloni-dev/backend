from django import forms

from .models import Lote, MovimientoStock


class RegistrarMovimientoAdminForm(forms.Form):
    lote = forms.ModelChoiceField(
        queryset=Lote.objects.select_related(
            "medicamento"
        ).order_by(
            "medicamento__nombre",
            "fecha_vencimiento",
        ),
    )

    tipo = forms.ChoiceField(
        choices=MovimientoStock.Tipo.choices,
    )

    cantidad = forms.IntegerField(
        min_value=1,
        max_value=2147483647,
        help_text="Cantidad de envases completos.",
    )

    motivo = forms.CharField(
        max_length=255,
        widget=forms.Textarea(
            attrs={"rows": 2}
        ),
    )

    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3}
        ),
    )