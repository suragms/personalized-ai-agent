from django.urls import path

from core.views import HealthView

urlpatterns = [path("", HealthView.as_view(), name="health")]
