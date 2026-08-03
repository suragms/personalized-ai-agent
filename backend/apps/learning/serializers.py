from rest_framework import serializers

from .models import LearningItem, LearningRoadmap, LearningSuggestion


class LearningItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningItem
        fields = ("id", "kind", "title", "url", "reason", "priority", "completed", "completed_at", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class LearningSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSuggestion
        fields = ("id", "date", "kind", "title", "reason", "source", "created_at")
        read_only_fields = ("id", "created_at")


class LearningRoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningRoadmap
        fields = ("id", "title", "level", "items", "created_at")
        read_only_fields = ("id", "created_at")
