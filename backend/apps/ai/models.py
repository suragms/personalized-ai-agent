from django.db import models
from django.conf import settings
from django.db.models import JSONField

from core.models import OwnedModel
from core.fields import EncryptedCharField


class ProviderDefinition(models.Model):
    """Catalog of supported LLM platforms."""

    CATEGORY_CHOICES = (
        ("cloud", "Cloud"),
        ("local", "Local"),
        ("custom", "Custom"),
    )

    PROTOCOL_CHOICES = (
        ("openai_chat", "OpenAI Chat"),
        ("openai_responses", "OpenAI Responses"),
        ("anthropic", "Anthropic"),
        ("gemini", "Gemini"),
        ("ollama", "Ollama"),
        ("custom", "Custom"),
    )

    id = models.SlugField(primary_key=True)
    display_name = models.CharField(max_length=128)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default="cloud")
    protocol = models.CharField(max_length=64, choices=PROTOCOL_CHOICES, default="openai_chat")
    requires_api_key = models.BooleanField(default=True)
    supports_model_discovery = models.BooleanField(default=False)
    supports_streaming = models.BooleanField(default=False)
    supports_tools = models.BooleanField(default=False)
    supports_embeddings = models.BooleanField(default=False)
    default_base_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)

    def __str__(self):
        return self.display_name


class ProviderConnection(OwnedModel):
    """A user's specific credentials and model settings for a provider."""

    provider = models.ForeignKey(ProviderDefinition, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=255, blank=True)
    base_url = models.URLField(blank=True)
    model = models.CharField(max_length=255, blank=True)

    # Encrypted fields
    api_key = EncryptedCharField(max_length=1024, blank=True)

    enabled = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Diagnostics
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    capabilities = JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.owner.username} - {self.provider.display_name}"

    def save(self, *args, **kwargs):
        # If this is marked as default, unset others for this user
        if self.is_default:
            ProviderConnection.objects.filter(owner=self.owner, is_default=True).exclude(pk=self.id).update(is_default=False)
        super().save(*args, **kwargs)

class UserSkillConfig(OwnedModel):
    """User-specific enablement and configuration for a discovered skill."""
    skill_id = models.CharField(max_length=255, db_index=True)
    enabled = models.BooleanField(default=True)
    configuration = JSONField(default=dict, blank=True)
    
    class Meta(OwnedModel.Meta):
        unique_together = (("owner", "skill_id"),)
        
    def __str__(self):
        return f"{self.owner.username} - {self.skill_id}"

class SkillExecutionLog(OwnedModel):
    """Safe metadata tracking for skill executions."""
    skill_id = models.CharField(max_length=255)
    skill_version = models.CharField(max_length=64, blank=True)
    
    started_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=64) # 'running', 'success', 'error', 'rejected'
    
    provider_id = models.CharField(max_length=128, blank=True)
    model = models.CharField(max_length=255, blank=True)
    error_code = models.CharField(max_length=128, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    request_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    def __str__(self):
        return f"{self.skill_id} [{self.status}]"
