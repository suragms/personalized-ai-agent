from django.urls import path

from .views import CommandView, ProviderStatusView

urlpatterns = [
    path("command/", CommandView.as_view(), name="ai_command"),
    path("providers/", ProviderStatusView.as_view(), name="ai_providers"),
]
