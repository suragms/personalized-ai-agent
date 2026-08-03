from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .exporters import export_docx, export_pdf
from .models import ResumeVersion
from .serializers import ResumeVersionSerializer
from .services import latest_resume, update_resume


class ResumeVersionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResumeVersionSerializer

    def get_queryset(self):
        return ResumeVersion.objects.filter(owner=self.request.user)

    @action(detail=False, methods=["post"])
    def regenerate(self, request):
        version = update_resume(request.user)
        return Response(ResumeVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        resume = self.get_object()
        fmt = request.query_params.get("format", "pdf").lower()
        exporter = {"pdf": export_pdf, "docx": export_docx}.get(fmt)
        if exporter is None:
            return Response({"detail": "Supported formats: pdf, docx."}, status=status.HTTP_400_BAD_REQUEST)
        data, media_type, filename = exporter(resume)
        return FileResponse(data, content_type=media_type, as_attachment=True, filename=filename)


class LatestResumeView(APIView):
    def get(self, request):
        resume = latest_resume(request.user)
        if resume is None:
            return Response({"detail": "No resume yet. POST /api/resume/versions/update/ to generate one."}, status=404)
        return Response(ResumeVersionSerializer(resume).data)
