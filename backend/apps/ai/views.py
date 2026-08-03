from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .command_router import route_command
from .providers import available_providers


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


class ProviderStatusView(APIView):
    """GET → list of configured LLM providers and their availability."""

    def get(self, request):
        return Response({"providers": available_providers()})
