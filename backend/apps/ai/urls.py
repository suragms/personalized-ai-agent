from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CommandView, ProviderConnectionViewSet

router = DefaultRouter()
router.register(r"providers", ProviderConnectionViewSet, basename="ai-providers")

urlpatterns = [
    path("command/", CommandView.as_view(), name="ai_command"),
    path("", include(router.urls)),
]
