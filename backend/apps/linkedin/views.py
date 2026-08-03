from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LinkedInProfile, PostIdea, ProfileScore
from .serializers import LinkedInProfileSerializer, PostIdeaSerializer, ProfileScoreSerializer
from .services import analyze_profile, best_posting_time, generate_post


class LinkedInProfileView(APIView):
    """GET/PUT the owner's LinkedIn profile."""

    def get(self, request):
        profile, _ = LinkedInProfile.objects.get_or_create(owner=request.user)
        return Response(LinkedInProfileSerializer(profile).data)

    def put(self, request):
        profile, _ = LinkedInProfile.objects.get_or_create(owner=request.user)
        serializer = LinkedInProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AnalysisView(APIView):
    """GET → run/refresh the profile analysis."""

    def get(self, request):
        result = analyze_profile(request.user)
        return Response(result.data)


class PostIdeaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostIdeaSerializer

    def get_queryset(self):
        return PostIdea.objects.filter(owner=self.request.user)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        post = generate_post(request.user)
        return Response(PostIdeaSerializer(post).data, status=status.HTTP_201_CREATED)


class PostingTimeView(APIView):
    def get(self, request):
        return Response(best_posting_time())


class ScoreHistoryView(APIView):
    def get(self, request):
        scores = ProfileScore.objects.filter(owner=request.user)[:30]
        return Response(ProfileScoreSerializer(scores, many=True).data)
