from rest_framework.routers import DefaultRouter

from .views import ConsultaViewSet


router = DefaultRouter()
router.register(
    "consultas",
    ConsultaViewSet,
    basename="consulta",
)

urlpatterns = router.urls