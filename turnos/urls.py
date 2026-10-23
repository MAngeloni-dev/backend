from rest_framework.routers import DefaultRouter

from .views import TurnoViewSet

router = DefaultRouter()
router.register(
    "turnos",
    TurnoViewSet,
    basename="turno",
)

urlpatterns = router.urls