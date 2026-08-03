from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NotificationRuleViewSet, NotificationViewSet, SweepView, UnreadView

# The "rules" router must be registered before the catch-all "" router so its
# ^rules/ patterns are matched first (the "" router's ^(?P<pk>[^/.]+)/$ would
# otherwise treat "rules" as a notification pk).
router = DefaultRouter()
router.register("rules", NotificationRuleViewSet, basename="notification-rules")
router.register("", NotificationViewSet, basename="notifications")

urlpatterns = [
    path("sweep/", SweepView.as_view(), name="notification-sweep"),
    path("unread/", UnreadView.as_view(), name="notification-unread"),
] + router.urls
