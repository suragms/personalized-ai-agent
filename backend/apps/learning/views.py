from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LearningItem, LearningRoadmap, LearningSuggestion
from .serializers import LearningItemSerializer, LearningRoadmapSerializer, LearningSuggestionSerializer
from .services import build_roadmap, daily_suggestions, top_trends


class LearningItemViewSet(viewsets.ModelViewSet):
    serializer_class = LearningItemSerializer

    def get_queryset(self):
        qs = LearningItem.objects.filter(owner=self.request.user)
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        item = self.get_object()
        item.completed = True
        from datetime import date

        item.completed_at = date.today()
        item.save(update_fields=["completed", "completed_at"])
        return Response(LearningItemSerializer(item).data)


class SuggestionsView(APIView):
    def get(self, request):
        suggestions = LearningSuggestion.objects.filter(owner=request.user)[:20]
        return Response(LearningSuggestionSerializer(suggestions, many=True).data)

    def post(self, request):
        suggestions = daily_suggestions(request.user)
        return Response(LearningSuggestionSerializer(suggestions, many=True).data)


class RoadmapView(APIView):
    def get(self, request):
        roadmap = LearningRoadmap.objects.filter(owner=request.user).first()
        if roadmap is None:
            roadmap = build_roadmap(request.user)
        return Response(LearningRoadmapSerializer(roadmap).data)


class TrendsView(APIView):
    def get(self, request):
        return Response({"trends": top_trends(request.user)})
