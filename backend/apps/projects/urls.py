from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MilestoneViewSet, ProjectViewSet, burndown_overview

router = DefaultRouter()
router.register("", ProjectViewSet, basename="projects")

# Explicit sub-resource routes must precede the router's catch-all detail
# pattern (^(?P<pk>[^/.]+)/$) so "milestones" is not treated as a project pk.
urlpatterns = [
    path("burndown/overview/", burndown_overview, name="burndown-overview"),
    path(
        "milestones/",
        MilestoneViewSet.as_view({"get": "list", "post": "create"}),
        name="milestone-list",
    ),
    path(
        "milestones/<uuid:pk>/",
        MilestoneViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="milestone-detail",
    ),
] + router.urls
