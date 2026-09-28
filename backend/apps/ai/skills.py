import os
import json
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ValidationError

from django.conf import settings

logger = logging.getLogger("ai")

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class SkillManifest(BaseModel):
    id: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    name: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    description: str
    category: str
    author: str = ""
    instructions: str = "" # Populated from SKILL.md
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_permissions: List[str] = Field(default_factory=list)
    required_integrations: List[str] = Field(default_factory=list)
    required_provider_capabilities: List[str] = Field(default_factory=list)
    tools: List[ToolDefinition] = Field(default_factory=list)
    configuration_schema: Dict[str, Any] = Field(default_factory=dict)
    safety_constraints: List[str] = Field(default_factory=list)
    enabled: bool = True

class SkillRegistryError(Exception):
    pass

class SkillRegistry:
    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir or os.path.join(settings.BASE_DIR, "skills")
        self._skills: Dict[str, SkillManifest] = {}

    def discover(self) -> Dict[str, str]:
        """Finds skills by looking for manifest.json in subdirectories."""
        found = {}
        if not os.path.exists(self.skills_dir):
            return found
            
        for d in os.listdir(self.skills_dir):
            path = os.path.join(self.skills_dir, d)
            if os.path.isdir(path):
                manifest_path = os.path.join(path, "manifest.json")
                skill_md_path = os.path.join(path, "SKILL.md")
                if os.path.exists(manifest_path):
                    found[d] = {
                        "manifest": manifest_path,
                        "skill_md": skill_md_path
                    }
        return found

    def load(self, clear=True):
        if clear:
            self._skills.clear()
            
        found = self.discover()
        errors = []
        
        for folder_name, paths in found.items():
            try:
                with open(paths["manifest"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Read SKILL.md if it exists
                instructions = ""
                if os.path.exists(paths["skill_md"]):
                    with open(paths["skill_md"], "r", encoding="utf-8") as f:
                        instructions = f.read()
                else:
                    errors.append({"folder": folder_name, "error": "Missing SKILL.md"})
                    continue
                    
                data["instructions"] = instructions
                
                # Check for ID mismatch between folder and ID
                if data.get("id") != folder_name:
                    errors.append({"folder": folder_name, "error": f"ID in manifest ({data.get('id')}) does not match folder name."})
                    continue

                # Validate schema via Pydantic
                manifest = SkillManifest(**data)
                
                # Check for duplicates
                if manifest.id in self._skills:
                    errors.append({"folder": folder_name, "error": f"Duplicate skill ID: {manifest.id}"})
                    continue
                    
                # Validate safe tools
                from .tools import TOOL_REGISTRY
                for t in manifest.tools:
                    if t.name not in TOOL_REGISTRY:
                        raise ValueError(f"Unsafe or unknown tool requested: {t.name}")
                
                self._skills[manifest.id] = manifest
                
            except json.JSONDecodeError as e:
                errors.append({"folder": folder_name, "error": f"Invalid JSON: {str(e)}"})
            except ValidationError as e:
                errors.append({"folder": folder_name, "error": f"Manifest validation error: {str(e)}"})
            except Exception as e:
                errors.append({"folder": folder_name, "error": str(e)})

        if errors:
            # We log but do not crash the app
            logger.warning(f"Skill registry encountered loading errors: {errors}")
            
        return {"loaded": len(self._skills), "errors": errors}

    def get(self, skill_id: str) -> Optional[SkillManifest]:
        return self._skills.get(skill_id)

    def list(self) -> List[SkillManifest]:
        return list(self._skills.values())

# Global registry instance
registry = SkillRegistry()

class SkillExecutor:
    def execute(self, user, skill_id: str, context: str):
        from django.utils import timezone
        from .models import UserSkillConfig, SkillExecutionLog
        from .permissions import check_permission, has_integration, check_provider_capabilities
        from .tools import TOOL_REGISTRY
        from .routing import AIRoutingService

        skill = registry.get(skill_id)
        if not skill:
            raise SkillRegistryError("SKILL_NOT_FOUND")

        # 1. Enabled check
        if not skill.enabled:
            raise SkillRegistryError("SKILL_DISABLED")
            
        config = UserSkillConfig.objects.filter(owner=user, skill_id=skill_id).first()
        if config and not config.enabled:
            raise SkillRegistryError("SKILL_DISABLED_BY_USER")

        # 2. Permission check
        for perm in skill.required_permissions:
            if not check_permission(user, perm):
                raise SkillRegistryError(f"PERMISSION_DENIED: {perm}")

        # 3. Integration check
        for integ in skill.required_integrations:
            if not has_integration(user, integ):
                raise SkillRegistryError(f"INTEGRATION_MISSING: {integ}")

        # 4. Provider capability check
        svc = AIRoutingService(user)
        conns = svc._get_connections_to_try()
        conn = conns[0] if conns else None
        
        # We don't crash if mock is used and capabilities are empty
        if conn and not check_provider_capabilities(conn, skill.required_provider_capabilities):
            raise SkillRegistryError("PROVIDER_CAPABILITY_MISSING")

        # Create log
        log = SkillExecutionLog.objects.create(
            owner=user,
            skill_id=skill.id,
            skill_version=skill.version,
            started_at=timezone.now(),
            status="running"
        )

        try:
            # 5. Configuration check
            # For this version, assume config is validated via Pydantic model if we had one
            # user_config = config.configuration if config else {}
            
            # 6. Execute (Simplest possible single-tool execution for v1)
            result_data = {}
            if skill.tools:
                tool_name = skill.tools[0].name
                if tool_name not in TOOL_REGISTRY:
                    raise SkillRegistryError(f"UNSAFE_TOOL: {tool_name}")
                tool_fn = TOOL_REGISTRY[tool_name]
                result_data = tool_fn(user, context=context)
            else:
                # Ask LLM if no explicit tool is given
                prompt = f"Instructions: {skill.instructions}\n\nTask: {context}"
                res = svc.complete("Execute the skill.", prompt)
                result_data = {"message": res, "data": {}}

            # Log success
            log.status = "success"
            log.completed_at = timezone.now()
            log.save()
            return result_data

        except Exception as e:
            log.status = "error"
            log.error_code = str(e)[:128]
            log.completed_at = timezone.now()
            log.save()
            raise SkillRegistryError(str(e))
