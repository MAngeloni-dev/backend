from rest_framework.routers import DefaultRouter

from .views import (
    LoteViewSet,
    MedicamentoViewSet,
    MovimientoStockViewSet,
)

router = DefaultRouter()

router.register(
    "medicamentos",
    MedicamentoViewSet,
    basename="medicamento",
)

router.register(
    "lotes",
    LoteViewSet,
    basename="lote",
)

router.register(
    "movimientos-stock",
    MovimientoStockViewSet,
    basename="movimiento-stock",
)

urlpatterns = router.urls