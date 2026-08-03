from rest_framework import serializers

from .models import LinkedInProfile, PostIdea, ProfileScore


class LinkedInProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedInProfile
        fields = ("id", "headline", "about", "location", "experience", "skills", "education", "certifications", "updated_at")
        read_only_fields = ("id", "updated_at")

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        profile, _ = LinkedInProfile.objects.update_or_create(owner=validated_data.pop("owner"), defaults=validated_data)
        return profile

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class ProfileScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileScore
        fields = ("id", "date", "score", "breakdown", "suggestions")


class PostIdeaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostIdea
        fields = ("id", "topic", "content", "hashtags", "source", "created_at")
        read_only_fields = ("id", "created_at")
