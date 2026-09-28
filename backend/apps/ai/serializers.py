from rest_framework import serializers
from .models import ProviderDefinition, ProviderConnection

class ProviderDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderDefinition
        fields = "__all__"

class ProviderConnectionSerializer(serializers.ModelSerializer):
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=ProviderDefinition.objects.all(), source="provider", write_only=True
    )
    provider_details = ProviderDefinitionSerializer(source="provider", read_only=True)
    # Write-only to avoid returning the plaintext API key. Masked value can be returned as a read-only field.
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_key_masked = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProviderConnection
        fields = (
            "id",
            "provider_id",
            "provider_details",
            "display_name",
            "base_url",
            "model",
            "api_key",
            "api_key_masked",
            "enabled",
            "is_default",
            "last_tested_at",
            "last_error_code",
            "latency_ms",
            "capabilities",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "last_tested_at", "last_error_code", "latency_ms", "capabilities", "created_at", "updated_at")

    def get_api_key_masked(self, obj) -> str:
        if not obj.api_key:
            return ""
        return f"{obj.api_key[:4]}...{obj.api_key[-4:]}" if len(obj.api_key) > 8 else "***"
        
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
