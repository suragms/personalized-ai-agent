from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .oauth import OAuthDisabledError, github_exchange, google_exchange
from .serializers import RegisterSerializer, UserSerializer


def _jwt_for(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


def _get_or_create_oauth_user(profile: dict) -> User:
    """Find an existing user by email/username or create one, linking the
    provider id to the username to keep accounts idempotent."""
    username = f"{profile['provider']}_{profile['provider_id']}"[:150]
    user = User.objects.filter(username=username).first()
    if user:
        return user
    email = profile["email"] or None
    user = User.objects.filter(email__iexact=email).first() if email else None
    if user is None:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=None,
            first_name=profile.get("name", ""),
            role=User.OWNER if not User.objects.exists() else User.VIEWER,
            github_username=profile.get("username", ""),
            avatar_url=profile.get("avatar_url", ""),
        )
    else:
        for field, value in (("avatar_url", profile.get("avatar_url", "")),):
            if value and not getattr(user, field):
                setattr(user, field, value)
        user.save(update_fields=[field])
    return user


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_jwt_for(user), status=status.HTTP_201_CREATED)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class OAuthBaseView(APIView):
    permission_classes = [AllowAny]
    exchange = None  # overridden

    def post(self, request):
        code = request.data.get("code", "")
        redirect_uri = request.data.get("redirect_uri", "")
        if not code:
            return Response({"detail": "`code` is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = self.exchange(code, redirect_uri)
        except OAuthDisabledError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"detail": f"OAuth failed: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        user = _get_or_create_oauth_user(profile)
        return Response(_jwt_for(user))


class GitHubOAuthView(OAuthBaseView):
    exchange = staticmethod(github_exchange)


class GoogleOAuthView(OAuthBaseView):
    exchange = staticmethod(google_exchange)
