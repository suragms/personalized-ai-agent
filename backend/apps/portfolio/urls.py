from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PortfolioProjectViewSet, PortfolioSettingsView

router = DefaultRouter()
router.register("projects", PortfolioProjectViewSet, basename="portfolio-projects")

urlpatterns = [
    path("settings/", PortfolioSettingsView.as_view(), name="portfolio-settings"),
] + router.urls
