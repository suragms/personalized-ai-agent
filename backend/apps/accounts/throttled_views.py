from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
