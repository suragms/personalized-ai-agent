from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalyticsSnapshot
from .services import module_analytics


class AnalyticsView(APIView):
    """GET /api/analytics/<module>/ where module ∈ overview|coding|projects|time|learning|linkedin|resume|business"""

    def get(self, request, module):
        try:
            data = module_analytics(request.user, module)
        except KeyError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(data)


class SnapshotHistoryView(APIView):
    def get(self, request, module):
        rows = AnalyticsSnapshot.objects.filter(owner=request.user, module=module)[:30]
        return Response(
            [{"date": r.date.isoformat(), "data": r.data} for r in rows]
        )
