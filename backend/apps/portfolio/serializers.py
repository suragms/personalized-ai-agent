from rest_framework import serializers

from .models import PortfolioProject, PortfolioSettings


class PortfolioProjectSerializer(serializers.ModelSerializer):
    repository = serializers.CharField(source="repository.full_name", read_only=True, allow_null=True)

    class Meta:
        model = PortfolioProject
        fields = (
            "id",
            "name",
            "description",
            "repository",
            "skills",
            "screenshots",
            "readme",
            "deployment_status",
            "live_url",
            "last_release_tag",
            "updated_at",
        )
        read_only_fields = ("id", "updated_at")

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class PortfolioSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioSettings
        fields = ("id", "headline", "bio", "theme", "sections_order", "updated_at")
        read_only_fields = ("id", "updated_at")
