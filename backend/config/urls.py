"""Root URL configuration — mounts the platform API under /api/."""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth
    path("api/auth/", include("accounts.urls")),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Platform modules
    path("api/ai/", include("ai.urls")),
    path("api/memory/", include("memory.urls")),
    path("api/github/", include("github.urls")),
    path("api/", include("productivity.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/linkedin/", include("linkedin.urls")),
    path("api/resume/", include("resume.urls")),
    path("api/portfolio/", include("portfolio.urls")),
    path("api/learning/", include("learning.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/notifications/", include("notifications.urls")),
]

# Health check used by Docker / Render.
urlpatterns += [path("api/health/", include("core.urls"))]
