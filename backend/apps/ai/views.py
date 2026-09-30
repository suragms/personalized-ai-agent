from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .command_router import route_command
from .models import ProviderConnection, ProviderDefinition, SkillExecutionLog, UserSkillConfig
from .providers import available_providers
from .serializers import ProviderConnectionSerializer, ProviderDefinitionSerializer
from .skills import SkillExecutor, registry


class CommandView(APIView):
    """POST {"command": "Generate today's report"} → structured CommandResult."""

    def post(self, request):
        text = (request.data.get("command") or "").strip()
        if not text:
            return Response({"detail": "`command` is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = route_command(text, request.user)
        return Response(
            {
                "intent": result.intent,
                "agent": result.agent,
                "matched": result.matched,
                "message": result.message,
                "data": result.data,
            }
        )


class ProviderConnectionViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderConnectionSerializer

    def get_queryset(self):
        return ProviderConnection.objects.filter(owner=self.request.user).order_by("-updated_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict):
            response.data["providers"] = available_providers()
        return response

    @action(detail=False, methods=["get"])
    def status(self, request):
        """Return configured environment providers status for Settings UI."""
        return Response({"providers": available_providers()})

    @action(detail=False, methods=["get"])
    def definitions(self, request):
        """Return available provider definitions (catalog)."""
        defs = ProviderDefinition.objects.all()
        serializer = ProviderDefinitionSerializer(defs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test connection for this specific provider configuration.

        Always returns 200 with ``{"status": "ok"|"error", ...}`` so the UI can
        render provider diagnostics without treating a provider failure as an
        API failure. ``code`` uses the AI_PROVIDER_* vocabulary.
        """
        conn = self.get_object()
        from core.connectivity import ai_error_code, normalize_exception, sanitize_error_message

        from .exceptions import AIProviderError
        from .services import AIRoutingService

        svc = AIRoutingService(request.user)
        try:
            res = svc.test_connection(conn)
            return Response(res)
        except AIProviderError as e:
            return Response({"status": "error", "code": e.code, "detail": sanitize_error_message(e)}, status=200)
        except Exception as e:
            status, _retryable, code = normalize_exception(e)
            return Response(
                {"status": "error", "code": ai_error_code(status, code), "detail": sanitize_error_message(e)},
                status=200,
            )


class SkillViewSet(viewsets.ViewSet):
    """ViewSet managing skills catalog, execution, and validation."""

    def list(self, request):
        registry.load()
        user = request.user
        configs = {c.skill_id: c.enabled for c in UserSkillConfig.objects.filter(owner=user)}
        manifests = []
        for s in registry.list():
            data = s.model_dump()
            data["enabled"] = configs.get(s.id, s.enabled)
            manifests.append(data)
        return Response(manifests)

    def retrieve(self, request, pk=None):
        registry.load()
        skill = registry.get(pk)
        if not skill:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        data = skill.model_dump()
        config = UserSkillConfig.objects.filter(owner=request.user, skill_id=pk).first()
        if config:
            data["enabled"] = config.enabled
        return Response(data)

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        UserSkillConfig.objects.update_or_create(owner=request.user, skill_id=pk, defaults={"enabled": True})
        return Response({"status": "enabled"})

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        UserSkillConfig.objects.update_or_create(owner=request.user, skill_id=pk, defaults={"enabled": False})
        return Response({"status": "disabled"})

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        registry.load()
        skill = registry.get(pk)
        if not skill:
            return Response({"valid": False, "errors": ["Skill not found"]}, status=404)
        return Response({"valid": True, "errors": []})

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        executor = SkillExecutor()
        context = request.data.get("context", "")
        try:
            res = executor.execute(request.user, pk, context)
            return Response({"status": "success", "data": res})
        except Exception as e:
            return Response({"status": "error", "error": str(e)}, status=400)

    @action(detail=False, methods=["get"])
    def executions(self, request):
        logs = SkillExecutionLog.objects.filter(owner=request.user).order_by("-started_at")[:50]
        data = [
            {
                "id": str(log.id),
                "skill_id": log.skill_id,
                "skill_version": log.skill_version,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "status": log.status,
                "error_code": log.error_code,
                "provider_id": log.provider_id,
                "model": log.model,
                "request_id": log.request_id,
                "latency_ms": log.latency_ms,
            }
            for log in logs
        ]
        return Response({"count": len(data), "results": data})
