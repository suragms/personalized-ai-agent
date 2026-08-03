import logging

from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .exporters import EXPORTERS
from .models import Report
from .serializers import ReportGenerateSerializer, ReportSerializer
from .services import generate_report

logger = logging.getLogger("reports")


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReportSerializer

    def get_queryset(self):
        qs = Report.objects.filter(owner=self.request.user)
        period = self.request.query_params.get("period")
        if period:
            qs = qs.filter(period=period)
        return qs

    @action(detail=False, methods=["post"])
    def generate(self, request):
        params = ReportGenerateSerializer(data=request.data)
        params.is_valid(raise_exception=True)
        period = params.validated_data["period"]
        result = generate_report(request.user, period=period)
        if result.status != "ok":
            return Response({"detail": result.summary}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        report_id = result.data.get("report_id")
        report = Report.objects.filter(owner=request.user, id=report_id).first() if report_id else None
        return Response(ReportSerializer(report).data if report else {"detail": result.summary}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        report = self.get_object()
        fmt = request.query_params.get("format", "md").lower()
        exporter = EXPORTERS.get(fmt)
        if exporter is None:
            return Response(
                {"detail": f"Unknown format '{fmt}'. Supported: {', '.join(EXPORTERS)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data, media_type, filename = exporter(report)
        except Exception as exc:  # pragma: no cover - exporter failures surface as 500
            logger.exception("Export failed for %s", fmt)
            return Response({"detail": f"Export failed: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response = FileResponse(data, content_type=media_type, as_attachment=True, filename=filename)
        return response
