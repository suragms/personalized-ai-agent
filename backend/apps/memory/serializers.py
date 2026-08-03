from rest_framework import serializers

from .models import ConversationLog, MemoryEntry, UserPreference


class MemoryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryEntry
        fields = ("id", "kind", "content", "metadata", "date", "created_at")
        read_only_fields = ("id", "created_at")


class MemoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryEntry
        fields = ("kind", "content", "metadata", "date")

    def create(self, validated_data):
        from .services import remember

        return remember(
            self.context["request"].user,
            validated_data.pop("content"),
            kind=validated_data.pop("kind", "note"),
            metadata=validated_data.pop("metadata", None),
        )


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, default="")
    k = serializers.IntegerField(required=False, default=8, min_value=1, max_value=50)


class ConversationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationLog
        fields = ("id", "role", "content", "intent", "created_at")


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ("id", "key", "value", "updated_at")
        read_only_fields = ("id", "updated_at")
