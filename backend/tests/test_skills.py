import json

import pytest

from ai.models import UserSkillConfig
from ai.skills import SkillExecutor, SkillManifest, SkillRegistry, SkillRegistryError


@pytest.fixture
def temp_skills_dir(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Valid skill
    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    manifest = {
        "id": "test-skill",
        "name": "Test Skill",
        "version": "1.0.0",
        "description": "Test description",
        "category": "test",
        "required_permissions": ["ai.generate"],
        "tools": [{"name": "get_current_time", "description": "", "input_schema": {}}]
    }
    (skill_dir / "manifest.json").write_text(json.dumps(manifest))
    (skill_dir / "SKILL.md").write_text("Test instructions")

    # Invalid skill - missing SKILL.md
    invalid_dir = skills_dir / "invalid-skill"
    invalid_dir.mkdir()
    invalid_manifest = {
        "id": "invalid-skill",
        "name": "Invalid",
        "version": "1.0.0",
        "description": "Test",
        "category": "test"
    }
    (invalid_dir / "manifest.json").write_text(json.dumps(invalid_manifest))

    return str(skills_dir)

@pytest.mark.django_db
def test_skill_registry_discovery(temp_skills_dir):
    registry = SkillRegistry(temp_skills_dir)
    found = registry.discover()

    assert "test-skill" in found
    assert "invalid-skill" in found

@pytest.mark.django_db
def test_skill_registry_load(temp_skills_dir):
    registry = SkillRegistry(temp_skills_dir)
    result = registry.load()

    assert result["loaded"] == 1
    assert len(result["errors"]) == 1
    assert "Missing SKILL.md" in result["errors"][0]["error"]

    skill = registry.get("test-skill")
    assert skill is not None
    assert skill.id == "test-skill"
    assert skill.instructions == "Test instructions"

@pytest.mark.django_db
def test_skill_execution_success(owner):
    from ai.skills import registry

    # Mock the registry with a test skill
    test_skill = SkillManifest(
        id="test-skill",
        name="Test Skill",
        version="1.0.0",
        description="Test",
        category="test",
        instructions="Test instructions",
        required_permissions=["ai.generate"],
        tools=[{"name": "get_current_time", "description": "", "input_schema": {}}]
    )
    registry._skills["test-skill"] = test_skill

    executor = SkillExecutor()
    result = executor.execute(owner, "test-skill", "test context")

    assert "time" in result

@pytest.mark.django_db
def test_skill_execution_permission_denied(viewer):
    from ai.skills import registry

    # Mock the registry with a test skill requiring ai.write
    test_skill = SkillManifest(
        id="restricted-skill",
        name="Restricted Skill",
        version="1.0.0",
        description="Test",
        category="test",
        instructions="Test instructions",
        required_permissions=["memory.write"],  # Viewers shouldn't have this
        tools=[{"name": "get_current_time", "description": "", "input_schema": {}}]
    )
    registry._skills["restricted-skill"] = test_skill

    executor = SkillExecutor()
    with pytest.raises(SkillRegistryError) as exc:
        executor.execute(viewer, "restricted-skill", "test context")

    assert "PERMISSION_DENIED" in str(exc.value)

@pytest.mark.django_db
def test_skill_execution_disabled_by_user(owner):
    from ai.skills import registry

    test_skill = SkillManifest(
        id="disabled-skill",
        name="Disabled Skill",
        version="1.0.0",
        description="Test",
        category="test",
        instructions="Test instructions",
        required_permissions=["ai.generate"],
        tools=[{"name": "get_current_time", "description": "", "input_schema": {}}]
    )
    registry._skills["disabled-skill"] = test_skill

    # Disable for this user
    UserSkillConfig.objects.create(owner=owner, skill_id="disabled-skill", enabled=False)

    executor = SkillExecutor()
    with pytest.raises(SkillRegistryError) as exc:
        executor.execute(owner, "disabled-skill", "test context")

    assert "SKILL_DISABLED_BY_USER" in str(exc.value)

@pytest.mark.django_db
def test_skill_execution_integration_missing(owner):
    from ai.skills import registry

    test_skill = SkillManifest(
        id="github-skill",
        name="GitHub Skill",
        version="1.0.0",
        description="Test",
        category="test",
        instructions="Test instructions",
        required_permissions=["ai.generate"],
        required_integrations=["github"],
        tools=[{"name": "get_current_time", "description": "", "input_schema": {}}]
    )
    registry._skills["github-skill"] = test_skill

    # Owner doesn't have github_username set
    executor = SkillExecutor()
    with pytest.raises(SkillRegistryError) as exc:
        executor.execute(owner, "github-skill", "test context")

    assert "INTEGRATION_MISSING: github" in str(exc.value)
