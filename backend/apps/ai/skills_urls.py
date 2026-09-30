from rest_framework.routers import DefaultRouter

from .views import SkillViewSet

router = DefaultRouter()
router.register(r"", SkillViewSet, basename="skills")

urlpatterns = router.urls
