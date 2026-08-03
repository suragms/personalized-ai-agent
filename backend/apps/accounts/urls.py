from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import GitHubOAuthView, GoogleOAuthView, MeView, RegisterView

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("oauth/github/", GitHubOAuthView.as_view(), name="oauth_github"),
    path("oauth/google/", GoogleOAuthView.as_view(), name="oauth_google"),
]
