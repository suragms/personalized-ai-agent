import pytest

from github.models import Repository
from github.services import at_risk_repositories, compute_productivity_score, weekly_analytics


@pytest.mark.django_db
def test_productivity_score_positive(seeded):
    score = compute_productivity_score(seeded)
    assert 0 <= score <= 100
    assert score > 50  # seeded dataset is productive


@pytest.mark.django_db
def test_weekly_analytics_shape(seeded):
    data = weekly_analytics(seeded, weeks=4)
    assert data["totals"]["commits"] > 0
    assert len(data["daily"]) > 0
    assert len(data["repos"]) >= 4


@pytest.mark.django_db
def test_at_risk_detects_inactive(seeded):
    risky = at_risk_repositories(seeded)
    names = [r["name"] for r in risky]
    assert any("legacy-dashboard" in n for n in names)


@pytest.mark.django_db
def test_repo_status_refresh(seeded):
    Repository.objects.filter(owner=seeded, full_name="hexastack/legacy-dashboard").update(status="active")
    risky = at_risk_repositories(seeded)
    legacy = next(r for r in risky if "legacy-dashboard" in r["name"])
    assert legacy["status"] == "inactive"
