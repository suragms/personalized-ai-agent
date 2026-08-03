from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PortfolioProject, PortfolioSettings
from .serializers import PortfolioProjectSerializer, PortfolioSettingsSerializer
from .services import refresh_portfolio


class PortfolioProjectViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioProjectSerializer

    def get_queryset(self):
        return PortfolioProject.objects.filter(owner=self.request.user).select_related("repository")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        projects = refresh_portfolio(request.user)
        return Response(PortfolioProjectSerializer(projects, many=True).data)


class PortfolioSettingsView(APIView):
    def get(self, request):
        settings, _ = PortfolioSettings.objects.get_or_create(owner=request.user)
        return Response(PortfolioSettingsSerializer(settings).data)

    def put(self, request):
        settings, _ = PortfolioSettings.objects.get_or_create(owner=request.user)
        serializer = PortfolioSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
