from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LatestResumeView, ResumeVersionViewSet

router = DefaultRouter()
router.register("versions", ResumeVersionViewSet, basename="resume-versions")

urlpatterns = [
    path("latest/", LatestResumeView.as_view(), name="resume-latest"),
] + router.urls
