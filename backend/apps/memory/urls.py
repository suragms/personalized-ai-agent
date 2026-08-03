from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ConversationsView, MemorySearchView, MemoryViewSet, PreferencesView

router = DefaultRouter()
router.register("", MemoryViewSet, basename="memory")

urlpatterns = [
    path("search/", MemorySearchView.as_view(), name="memory_search"),
    path("conversations/", ConversationsView.as_view(), name="memory_conversations"),
    path("preferences/", PreferencesView.as_view(), name="memory_preferences"),
] + router.urls
