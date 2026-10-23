from rest_framework.routers import DefaultRouter

from .views import (
    EvolucionInternacionViewSet,
    InternacionViewSet,
)

router = DefaultRouter()

router.register(
    "internaciones",
    InternacionViewSet,
    basename="internacion",
)

router.register(
    "evoluciones-internacion",
    EvolucionInternacionViewSet,
    basename="evolucion-internacion",
)

urlpatterns = router.urls