from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LearningItemViewSet, RoadmapView, SuggestionsView, TrendsView

router = DefaultRouter()
router.register("items", LearningItemViewSet, basename="learning-items")

urlpatterns = [
    path("suggestions/", SuggestionsView.as_view(), name="learning-suggestions"),
    path("roadmap/", RoadmapView.as_view(), name="learning-roadmap"),
    path("trends/", TrendsView.as_view(), name="learning-trends"),
] + router.urls
