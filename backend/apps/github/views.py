from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Commit, GithubInsight, Issue, PullRequest, Release, Repository
from .serializers import (
    CommitSerializer,
    GithubInsightSerializer,
    IssueSerializer,
    PullRequestSerializer,
    ReleaseSerializer,
    RepositorySerializer,
)
from .services import at_risk_repositories, contribution_graph, weekly_analytics


class RepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RepositorySerializer

    def get_queryset(self):
        return Repository.objects.filter(owner=self.request.user).select_related("owner")


class CommitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommitSerializer

    def get_queryset(self):
        qs = Commit.objects.filter(owner=self.request.user).select_related("repository")
        repo = self.request.query_params.get("repository")
        if repo:
            qs = qs.filter(repository__full_name=repo)
        return qs


class PullRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PullRequestSerializer

    def get_queryset(self):
        qs = PullRequest.objects.filter(owner=self.request.user).select_related("repository")
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        return qs


class IssueViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IssueSerializer

    def get_queryset(self):
        qs = Issue.objects.filter(owner=self.request.user).select_related("repository")
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        return qs


class ReleaseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        return Release.objects.filter(owner=self.request.user).select_related("repository")


@api_view(["GET"])
def analytics(request):
    weeks = int(request.query_params.get("weeks", 8))
    return Response(weekly_analytics(request.user, weeks=min(weeks, 26)))


@api_view(["GET"])
def health(request):
    return Response({"repositories": at_risk_repositories(request.user)})


@api_view(["GET"])
def insights(request):
    data = list(GithubInsight.objects.filter(owner=request.user)[:20])
    return Response(GithubInsightSerializer(data, many=True).data)


@api_view(["GET"])
def contributions(request):
    days = int(request.query_params.get("days", 90))
    return Response(contribution_graph(request.user, days=min(days, 365)))
