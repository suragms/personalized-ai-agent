from rest_framework import serializers

from .models import ResumeVersion


class ResumeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeVersion
        fields = (
            "id",
            "version_number",
            "full_name",
            "title",
            "summary",
            "contact",
            "experience",
            "projects",
            "education",
            "skills",
            "ats_score",
            "keywords_missing",
            "content",
            "created_at",
        )
        read_only_fields = fields
