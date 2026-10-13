from rest_framework.routers import DefaultRouter

from .views import (
    EspecieViewSet,
    PacienteViewSet,
    RazaViewSet,
    TutorViewSet,
)


router = DefaultRouter()
router.register("tutores", TutorViewSet, basename="tutor")
router.register("especies", EspecieViewSet, basename="especie")
router.register("razas", RazaViewSet, basename="raza")
router.register("pacientes", PacienteViewSet, basename="paciente")

urlpatterns = router.urls