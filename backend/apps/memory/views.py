from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConversationLog, MemoryEntry, UserPreference
from .serializers import (
    ConversationLogSerializer,
    MemoryEntrySerializer,
    MemoryWriteSerializer,
    SearchSerializer,
    UserPreferenceSerializer,
)
from .services import log_conversation, search_memory, set_preference


class MemoryViewSet(viewsets.ModelViewSet):
    """CRUD over the owner's memory entries."""

    serializer_class = MemoryEntrySerializer
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return MemoryEntry.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MemoryWriteSerializer
        return MemoryEntrySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class MemorySearchView(APIView):
    """GET ?query=...&k=8 → {mode, message, results}.

    `mode` reports how the ranking was produced (semantic | keyword | recent);
    fallbacks are disclosed instead of passing silently for semantic results.
    """

    def get(self, request):
        params = SearchSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        query = params.validated_data.get("query", "")
        k = params.validated_data.get("k", 8)
        result = search_memory(request.user, query, k=k) if query else None
        if result is None:
            return Response({"mode": "none", "message": "No query provided.", "results": []})
        return Response(
            {
                "mode": result.mode,
                "message": result.message,
                "results": MemoryEntrySerializer(result.entries, many=True).data,
            }
        )


class ConversationsView(APIView):
    """GET recent conversation log; POST {role, content, intent} to append."""

    def get(self, request):
        logs = ConversationLog.objects.filter(owner=request.user)[:50]
        return Response(ConversationLogSerializer(logs, many=True).data)

    def post(self, request):
        role = request.data.get("role", "user")
        content = request.data.get("content", "")
        intent = request.data.get("intent", "")
        if not content:
            return Response({"detail": "`content` is required."}, status=status.HTTP_400_BAD_REQUEST)
        log_conversation(request.user, role, content, intent)
        return Response({"detail": "logged"}, status=status.HTTP_201_CREATED)


class PreferencesView(APIView):
    """GET all preferences; PUT {key, value} to upsert one."""

    def get(self, request):
        prefs = UserPreference.objects.filter(owner=request.user)
        return Response(UserPreferenceSerializer(prefs, many=True).data)

    def put(self, request):
        key = request.data.get("key", "")
        value = request.data.get("value", {})
        if not key:
            return Response({"detail": "`key` is required."}, status=status.HTTP_400_BAD_REQUEST)
        pref = set_preference(request.user, key, value)
        return Response(UserPreferenceSerializer(pref).data)
