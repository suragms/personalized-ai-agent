import pytest

from ai.command_router import route_command


@pytest.mark.django_db
def test_route_github_summary(seeded):
    result = route_command("How many commits did I make this week?", seeded)
    assert result.matched and result.intent == "github_summary"
    assert result.data["totals"]["commits"] > 0


@pytest.mark.django_db
def test_route_repo_attention(seeded):
    result = route_command("Which repository needs attention?", seeded)
    assert result.matched and result.intent == "github_attention"
    assert result.data["repos"]  # seeded has an inactive repo


@pytest.mark.django_db
def test_route_unknown_intent(seeded):
    result = route_command("juggle some kittens on the moon", seeded)
    assert result.matched is False
    assert result.intent == "help"


@pytest.mark.django_db
def test_route_daily_report(seeded):
    result = route_command("Generate today's report", seeded)
    assert result.intent == "generate_report"
    assert "report" in result.data
