from rest_framework import serializers

from .models import Notification, NotificationRule


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "kind", "title", "body", "severity", "link", "read", "created_at")
        read_only_fields = ("id", "created_at")


class NotificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRule
        fields = ("id", "rule_type", "enabled", "threshold", "updated_at")
        read_only_fields = ("id", "updated_at")
