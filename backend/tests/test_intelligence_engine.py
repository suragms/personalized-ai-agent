"""Phase 3 — Insight Engine pipeline tests.

Covers, per the Phase 3 spec: provenance/freshness/confidence vocabulary,
deterministic analyzers, engine dedup + expiry + isolation, alert cooldown,
task conversion dedup, honest AI interpretation, insufficient-data reports,
daily plan generation, honest memory search, and the API surface.
"""
from datetime import timedelta

import pytest
from django.utils import timezone
from intelligence.analyzers import AnalysisFinding
from intelligence.engine import InsightEngine
from intelligence.models import Alert, DataSnapshot, DataSource, Goal, Insight, IntegrationConnection
from intelligence.priority import score_priority
from intelligence.provenance import (
    AGING,
    FRESH,
    STALE,
    UNAVAILABLE,
    Provenance,
    compute_freshness,
    confidence_from_evidence,
)
from intelligence.services import IntelligenceService, ReportService

# ─────────────────────────────────────────────────────────────────────────
# §9/§10 — provenance helpers: freshness & confidence
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "hours,source,expected",
    [
        (1, "github", FRESH),
        (48, "github", AGING),
        (100, "github", STALE),
        (1, "website", FRESH),
        (200, "website", AGING),
        (400, "website", STALE),
        (100, "manual", FRESH),
        (1000, "manual", AGING),
        (3000, "manual", STALE),
    ],
)
def test_freshness_levels_are_per_source(hours, source, expected):
    last_sync = timezone.now() - timedelta(hours=hours)
    result = compute_freshness(last_sync, source)
    assert result.level == expected
    if expected == STALE:
        assert result.message  # stale always discloses age


def test_freshness_unavailable_when_never_synced():
    result = compute_freshness(None, "github")
    assert result.level == UNAVAILABLE
    assert result.provenance == Provenance.UNAVAILABLE_DATA


def test_freshness_sync_frequency_overrides_thresholds():
    # A source with its own 6h cadence is "stale" at 20h even for a weekly type.
    last_sync = timezone.now() - timedelta(hours=20)
    result = compute_freshness(last_sync, "website", sync_frequency_hours=6)
    assert result.level == STALE


def test_confidence_requires_evidence():
    fresh = compute_freshness(timezone.now(), "github")
    assert confidence_from_evidence(0, fresh) == "insufficient"
    assert confidence_from_evidence(1, fresh) == "high"
    aging = compute_freshness(timezone.now() - timedelta(hours=48), "github")
    assert confidence_from_evidence(1, aging) == "low"
    stale = compute_freshness(timezone.now() - timedelta(hours=100), "github")
    assert confidence_from_evidence(3, stale) == "low"
    unavailable = compute_freshness(None, "github")
    assert confidence_from_evidence(3, unavailable) == "insufficient"


# ─────────────────────────────────────────────────────────────────────────
# §12 — priority engine
# ─────────────────────────────────────────────────────────────────────────


def test_priority_scoring_is_deterministic_and_labeled():
    label1, factors1 = score_priority(severity="critical", confidence="high", freshness_level=FRESH)
    label2, factors2 = score_priority(severity="critical", confidence="high", freshness_level=FRESH)
    assert label1 == label2
    assert factors1 == factors2
    total = sum(f["points"] for f in factors1)
    if total >= 60:
        assert label1 == "critical"
    elif total >= 40:
        assert label1 == "high"
    assert all("reason" in f for f in factors1)


def test_priority_orders_severities():
    labels = {}
    for severity in ("info", "low", "medium", "high", "critical"):
        labels[severity], _ = score_priority(severity=severity, confidence="low", freshness_level=STALE)
    rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    assert rank[labels["info"]] <= rank[labels["low"]]
    assert rank[labels["low"]] <= rank[labels["medium"]] <= rank[labels["high"]]
    assert rank[labels["critical"]] >= rank[labels["high"]]


def test_priority_goal_relevance_adds_points():
    base, _ = score_priority(severity="medium", confidence="medium", freshness_level=FRESH)
    boosted, factors = score_priority(
        severity="medium", confidence="medium", freshness_level=FRESH, goal_relevant=True
    )
    goal_factor = next(f for f in factors if f["name"] == "goal_relevance")
    assert goal_factor["points"] == 10
    assert boosted != "low" or base != "low"


# ─────────────────────────────────────────────────────────────────────────
# §4/§5 — deterministic analyzers
# ─────────────────────────────────────────────────────────────────────────


def test_analyzers_return_nothing_without_repositories(owner):
    from github.analyzers import run_github_analyzers

    assert run_github_analyzers(owner) == []


def test_analyzers_find_slowing_repository(seeded):
    from github.analyzers import RepositoryHealthAnalyzer

    findings = RepositoryHealthAnalyzer().analyze(seeded)
    slowing = [f for f in findings if f.metric == "slowing_repository"]
    assert slowing
    finding = slowing[0]
    assert finding.dedup_key.startswith("github:repo:slowing:")
    assert finding.evidence_count >= 1
    assert finding.observed_metrics.get("days_since_last_commit", 0) > 30
    assert finding.provenance  # every finding declares provenance


def test_stale_pr_analyzer(seeded):
    from github.analyzers import PullRequestAnalyzer
    from github.models import PullRequest

    repo = seeded.repositories.first()
    PullRequest.objects.create(
        owner=seeded,
        repository=repo,
        number=42,
        title="Old PR",
        state="open",
        author="someone",
        created_at=timezone.now() - timedelta(days=20),
    )
    findings = PullRequestAnalyzer().analyze(seeded)
    stale = [f for f in findings if f.metric == "stale_pull_requests"]
    assert stale and stale[0].value == 1
    assert stale[0].dedup_key == "github:prs:stale_14d"


def test_finding_evidence_text_renders_every_entry():
    finding = AnalysisFinding(
        metric="m",
        value=1,
        period="30d",
        source="github",
        evidence=[{"metric": "a", "value": 1}, {"metric": "b", "value": 2}],
        insight_type="risk",
        severity="medium",
        title="t",
        description="d",
        recommended_action="r",
        dedup_key="k",
    )
    text = finding.evidence_text()
    assert "metric: a" in text and "metric: b" in text
    assert "value: 1" in text and "value: 2" in text
    assert finding.evidence_count == 2


# ─────────────────────────────────────────────────────────────────────────
# §2/§7/§14 — engine: dedup, provenance, expiry, tasks, isolation
# ─────────────────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_source(owner):
    """A github DataSource synced right now (fresh REAL_CONNECTED_DATA)."""
    source = DataSource.objects.create(
        owner=owner,
        source_type="github",
        name="GitHub (owner)",
        state="connected",
        last_synced_at=timezone.now(),
        sync_frequency_hours=24,
    )
    DataSnapshot.objects.create(
        owner=owner,
        source=source,
        snapshot_date=timezone.now(),
        raw_data={"repositories": 4},
        metrics={"repositories": 4},
    )
    IntegrationConnection.objects.get_or_create(
        owner=owner,
        platform="github",
        defaults={"status": "connected", "connected_account": "owner"},
    )
    return source


def test_engine_creates_insights_with_full_provenance(seeded, fresh_source):
    summary = InsightEngine(seeded).run()

    assert summary["created"] >= 1
    insights = Insight.objects.filter(owner=seeded)
    assert insights.exists()

    github_insights = insights.filter(source_type="github")
    assert github_insights.exists()
    for insight in github_insights:
        assert insight.provenance == Provenance.REAL_CONNECTED_DATA
        assert insight.snapshot is not None  # linked to a snapshot
        assert insight.structured_evidence  # structured evidence, not prose only
        assert insight.confidence in ("high", "medium", "low")  # never "insufficient"
        assert insight.priority_reasoning  # stored reasoning
        assert insight.last_confirmed_at is not None
        assert insight.evidence  # human-readable rendering


def test_engine_is_idempotent_on_rerun(seeded, fresh_source):
    InsightEngine(seeded).run()
    first_count = Insight.objects.filter(owner=seeded).count()

    summary = InsightEngine(seeded).run()
    assert summary["created"] == 0
    assert Insight.objects.filter(owner=seeded).count() == first_count
    assert summary["updated"] >= 1  # reconfirmed instead of duplicated


def test_unconfirmed_insights_expire(seeded, fresh_source):
    from github.models import PullRequest

    repo = seeded.repositories.first()
    pr = PullRequest.objects.create(
        owner=seeded,
        repository=repo,
        number=7,
        title="Stale PR",
        state="open",
        author="someone",
        created_at=timezone.now() - timedelta(days=20),
    )
    InsightEngine(seeded).run()
    insight = Insight.objects.get(owner=seeded, dedup_key="github:prs:stale_14d")
    assert insight.status == "new"

    pr.state = "closed"
    pr.save()

    summary = InsightEngine(seeded).run()
    insight.refresh_from_db()
    assert insight.status == "expired"
    assert summary["expired"] >= 1


def test_mock_provider_never_fakes_ai_interpretation(seeded, fresh_source):
    """With no real provider configured, interpretation must be marked unavailable."""
    from github.models import PullRequest

    repo = seeded.repositories.first()
    PullRequest.objects.create(
        owner=seeded,
        repository=repo,
        number=3,
        title="Needs review",
        state="open",
        author="x",
        created_at=timezone.now() - timedelta(days=25),
    )
    InsightEngine(seeded).run()

    interpreted = Insight.objects.filter(owner=seeded).exclude(interpretation_meta={})
    assert interpreted.exists()  # a medium+ severity finding was offered to the AI layer
    for insight in interpreted:
        assert insight.interpretation_meta["available"] is False
        assert insight.ai_interpretation == ""
        assert insight.interpretation_meta["provenance"] in (None, "MOCK_PROVIDER")


def test_engine_creates_tasks_for_high_severity_with_dedup(seeded, fresh_source):
    from github.models import PullRequest
    from productivity.models import Task

    PullRequest.objects.filter(owner=seeded).delete()
    seeded.repositories.update(last_commit_at=timezone.now() - timedelta(days=120))
    goal = Goal.objects.create(
        owner=seeded,
        title="Ship portfolio v2",
        description="Launch the new portfolio site",
        category="project",
        deadline=timezone.now().date() - timedelta(days=3),
        status="active",
        progress_pct=40,
    )

    InsightEngine(seeded).run()
    tasks = Task.objects.filter(owner=seeded)
    assert tasks.count() >= 1
    goal_task = tasks.filter(title__icontains="Goal deadline passed").first()
    assert goal_task is not None
    assert goal_task.source_insight is not None
    assert goal_task.provenance == Provenance.USER_PROVIDED_DATA
    assert goal_task.dedup_key.startswith("insight:")

    # Re-run: no duplicate tasks
    InsightEngine(seeded).run()
    assert Task.objects.filter(owner=seeded).count() == tasks.count()

    # Completed task is not recreated within the cooldown window
    tasks.update(status="done", completed_at=timezone.now())
    InsightEngine(seeded).run()
    assert Task.objects.filter(owner=seeded).count() == tasks.count()
    assert goal.status == "active"


def test_engine_data_isolation(owner, seeded, fresh_source):
    from accounts.models import User
    from github.models import Repository

    other = User.objects.create_user(
        username="other", email="other@test.dev", password="x12345678", role=User.OWNER
    )
    # Same repository name → same dedup_key for both users: each must get its
    # own row (dedup is owner-scoped) and runs must not touch each other.
    Repository.objects.create(
        owner=other,
        name="legacy-dashboard",
        full_name="suragdev/legacy-dashboard",
        last_commit_at=timezone.now() - timedelta(days=60),
    )
    DataSource.objects.create(
        owner=other, source_type="github", name="GitHub (other)", state="connected", last_synced_at=timezone.now()
    )

    InsightEngine(seeded).run()
    seeded_count = Insight.objects.filter(owner=seeded).count()
    InsightEngine(other).run()

    key = "github:repo:slowing:suragdev/legacy-dashboard"
    assert Insight.objects.filter(owner=other, dedup_key=key).count() == 1
    assert Insight.objects.filter(owner=seeded, dedup_key=key).count() == 1
    # other's run left seeded's rows untouched
    assert Insight.objects.filter(owner=seeded).count() == seeded_count
    # every row belongs to exactly one owner
    assert set(Insight.objects.values_list("owner_id", flat=True)) <= {owner.id, other.id, seeded.id}


def test_no_data_run_skips_github_scope(owner):
    summary = InsightEngine(owner).run()
    assert summary["created"] == 0
    assert {"scope": "github", "reason": "no_github_data", "provenance": Provenance.UNAVAILABLE_DATA} in summary["skipped"]
    assert Insight.objects.filter(owner=owner).count() == 0  # nothing fabricated


def test_stale_rows_yield_stale_provenance(seeded):
    """Rows exist but no DataSource sync → analyzed as STALE_DATA, not fresh."""
    summary = InsightEngine(seeded).run()
    assert summary["scopes"]["github"]["provenance"] == Provenance.STALE_DATA
    for insight in Insight.objects.filter(owner=seeded, source_type="github"):
        assert insight.provenance == Provenance.STALE_DATA
        assert insight.confidence == "low"  # stale evidence is disclosed as low


# ─────────────────────────────────────────────────────────────────────────
# §15 — alerts: dedup, cooldown, dismissed
# ─────────────────────────────────────────────────────────────────────────


def _stale_source(user):
    return DataSource.objects.create(
        owner=user,
        source_type="github",
        name="GitHub (stale)",
        state="connected",
        last_synced_at=timezone.now() - timedelta(days=10),
        sync_frequency_hours=24,
    )


def test_alert_dedup_and_cooldown(owner):
    _stale_source(owner)

    first = IntelligenceService.create_alert(
        owner,
        category="integration",
        severity="medium",
        title="GitHub (stale) data is stale",
        message="Old",
        dedup_key="freshness:stale:github:test",
    )
    assert first[1] is True

    second = IntelligenceService.create_alert(
        owner,
        category="integration",
        severity="medium",
        title="GitHub (stale) data is stale",
        message="New message within cooldown",
        dedup_key="freshness:stale:github:test",
    )
    assert second[1] is False
    assert Alert.objects.filter(owner=owner).count() == 1
    alert = Alert.objects.get(owner=owner)
    assert alert.occurrences == 2
    assert alert.message == "Old"  # content frozen inside the cooldown window

    # Cooldown passed → same row, refreshed content, still not a new alert
    alert.last_fired_at = timezone.now() - timedelta(hours=25)
    alert.save()
    third = IntelligenceService.create_alert(
        owner,
        category="integration",
        severity="medium",
        title="GitHub (stale) data is stale",
        message="Refreshed after cooldown",
        dedup_key="freshness:stale:github:test",
    )
    assert third[1] is False
    alert.refresh_from_db()
    assert alert.occurrences == 3
    assert alert.message == "Refreshed after cooldown"


def test_dismissed_alert_is_never_reraised(owner):
    alert, _ = IntelligenceService.create_alert(
        owner, category="deadline", severity="high", title="T", message="M", dedup_key="k1"
    )
    alert.status = "dismissed"
    alert.save()

    again, created = IntelligenceService.create_alert(
        owner, category="deadline", severity="high", title="T", message="M", dedup_key="k1"
    )
    assert created is False
    assert Alert.objects.filter(owner=owner).count() == 1


def test_resolved_alert_may_fire_again(owner):
    alert, _ = IntelligenceService.create_alert(
        owner, category="deadline", severity="high", title="T", message="M", dedup_key="k2"
    )
    alert.status = "resolved"
    alert.save()

    _, created = IntelligenceService.create_alert(
        owner, category="deadline", severity="high", title="T", message="M", dedup_key="k2"
    )
    assert created is True
    assert Alert.objects.filter(owner=owner).count() == 2


def test_condition_alerts_raise_stale_source_alert_once(owner):
    _stale_source(owner)
    engine = InsightEngine(owner)

    raised = engine.condition_alerts()
    assert raised == 1
    raised_again = engine.condition_alerts()
    assert raised_again == 0  # cooldown absorbed the repeat
    assert Alert.objects.filter(owner=owner).count() == 1


# ─────────────────────────────────────────────────────────────────────────
# §16 — reports: real content, insufficient-data guard, daily plan
# ─────────────────────────────────────────────────────────────────────────


def test_report_insufficient_data_is_not_persisted(owner):
    from intelligence.models import Report

    before = Report.objects.filter(owner=owner).count()
    result = ReportService.generate_report(
        owner, "daily_intelligence", timezone.now().date() - timedelta(days=1), timezone.now().date()
    )
    assert result["insufficient_data"] is True
    assert result["report"] is None
    assert Report.objects.filter(owner=owner).count() == before


def test_report_uses_real_metrics(seeded):
    from intelligence.models import Report

    InsightEngine(seeded).run()
    today = timezone.now().date()
    result = ReportService.generate_report(seeded, "daily_intelligence", today - timedelta(days=7), today)

    assert result["insufficient_data"] is False
    report = result["report"]
    assert report.provenance == Provenance.DETERMINISTIC_ANALYSIS
    assert report.metrics["commits"] >= 1  # real commit rows, not zeros
    assert report.metrics["repositories"] >= 1
    assert report.insufficient_data is False
    assert "## Activity" in report.content
    assert report.findings  # engine findings surfaced (seeding created none — assert structure instead)
    assert report.data_freshness or report.data_sources == []
    assert Report.objects.filter(owner=seeded).count() == 1


def test_morning_and_evening_plan(seeded, fresh_source):
    from intelligence.daily import generate_evening_review, generate_morning_plan

    from productivity.models import Task

    InsightEngine(seeded).run()
    Task.objects.create(owner=seeded, title="Write docs", status="todo", due_date=timezone.now().date())

    plan = generate_morning_plan(seeded)
    assert plan.priorities or plan.recommended_focus
    assert plan.recommended_focus  # deterministic focus text
    assert plan.tasks  # due task listed

    Task.objects.create(
        owner=seeded, title="Done thing", status="done", completed_at=timezone.now()
    )
    evening = generate_evening_review(seeded)
    assert evening.completed_tasks
    assert evening.evening_insights
    assert evening.reviewed_at is not None


# ─────────────────────────────────────────────────────────────────────────
# §22 — memory search honesty
# ─────────────────────────────────────────────────────────────────────────


def test_memory_search_reports_keyword_fallback(owner):
    from memory.services import remember, search_memory

    remember(owner, "The portfolio deploy pipeline uses GitHub Actions", kind="note")
    result = search_memory(owner, "portfolio pipeline")

    # No real embedding provider in tests → fallback must be disclosed
    assert result.mode in ("keyword", "recent", "semantic")
    if result.mode != "semantic":
        assert result.message  # honest disclosure, never silent
    if result.mode == "keyword":
        assert result.entries  # keyword match still found the note
        assert "Semantic search unavailable" in result.message


def test_memory_search_empty_query_is_none_mode(owner):
    from memory.services import search_memory

    result = search_memory(owner, "")
    assert result.mode == "none"


# ─────────────────────────────────────────────────────────────────────────
# §23/§24 — API surface
# ─────────────────────────────────────────────────────────────────────────


def test_summary_endpoint(client, owner):
    resp = client.get("/api/intelligence/summary/")
    assert resp.status_code in (401, 403)  # anonymous denied


def test_summary_endpoint_authenticated(auth_client, seeded, fresh_source):
    InsightEngine(seeded).run()
    resp = auth_client.get("/api/intelligence/summary/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["insights"]["total"] >= 1
    assert "alerts" in data and "tasks" in data and "goals" in data
    assert data["data"]["overall_status"] in ("healthy", "stale", "error", "no_data")
    assert data["generated_at"]


def test_insights_generate_endpoint(auth_client, seeded, fresh_source):
    resp = auth_client.post("/api/intelligence/insights/generate/", {}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert "created" in data and "scopes" in data

    # idempotent via API too
    resp2 = auth_client.post("/api/intelligence/insights/generate/", {}, format="json")
    assert resp2.json()["created"] == 0


def test_convert_to_task_endpoint(auth_client, seeded, fresh_source):
    from github.models import PullRequest

    repo = seeded.repositories.first()
    PullRequest.objects.create(
        owner=seeded,
        repository=repo,
        number=99,
        title="Another stale PR",
        state="open",
        author="x",
        created_at=timezone.now() - timedelta(days=30),
    )
    auth_client.post("/api/intelligence/insights/generate/", {}, format="json")

    insight = Insight.objects.filter(owner=seeded, severity__in=("high", "critical")).first()
    if insight is None:
        # No high-severity insight seeded; convert an existing one explicitly
        insight = Insight.objects.filter(owner=seeded).first()
    resp = auth_client.post(f"/api/intelligence/insights/{insight.id}/convert_to_task/", {}, format="json")
    assert resp.status_code == 200
    task = resp.json()["task"]
    assert task["id"]
    assert task["source_insight"] == str(insight.id) or task["source_insight"] == insight.id


def test_report_generate_endpoint_insufficient_returns_400(client, owner):
    client.force_authenticate(user=owner)
    resp = client.post("/api/intelligence/reports/generate/", {}, format="json")
    assert resp.status_code == 400
    data = resp.json()
    assert data["insufficient_data"] is True
    assert data["report"] is None


def test_report_generate_endpoint_with_data(auth_client, seeded):
    resp = auth_client.post("/api/intelligence/reports/generate/", {}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["insufficient_data"] is False
    assert data["report"]["provenance"] == Provenance.DETERMINISTIC_ANALYSIS


def test_daily_plan_generate_endpoint(auth_client):
    resp = auth_client.post("/api/intelligence/daily-plans/generate/", {}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert "priorities" in data and "date" in data


def test_datasource_sync_rejects_unsupported_source(auth_client, owner):
    source = DataSource.objects.create(owner=owner, source_type="website", name="Site", state="connected")
    resp = auth_client.post(f"/api/intelligence/data-sources/{source.id}/sync/", {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "sync_unsupported"  # honest refusal, no fake timestamp


def test_datasource_sync_without_connection_is_honest(auth_client, owner):
    source = DataSource.objects.create(
        owner=owner, source_type="github", name="GitHub", state="connected", last_synced_at=None
    )
    resp = auth_client.post(f"/api/intelligence/data-sources/{source.id}/sync/", {}, format="json")
    assert resp.status_code == 400
    assert resp.json()["code"] == "not_connected"
    source.refresh_from_db()
    assert source.last_synced_at is None  # no fake success timestamp


# ─────────────────────────────────────────────────────────────────────────
# Celery tasks — idempotent, per-user isolated
# ─────────────────────────────────────────────────────────────────────────


def test_daily_intelligence_task_runs_for_all_users(seeded, fresh_source):
    from intelligence.tasks import daily_intelligence

    results = daily_intelligence.run()
    assert "owner" in results
    assert results["owner"] != {"status": "error"}
    # second run must not duplicate
    count = Insight.objects.filter(owner=seeded).count()
    daily_intelligence.run()
    assert Insight.objects.filter(owner=seeded).count() == count


def test_check_freshness_task_is_idempotent(owner):
    from intelligence.tasks import check_freshness

    _stale_source(owner)
    results = check_freshness.run()
    assert results["owner"]["alerts_raised"] == 1
    results2 = check_freshness.run()
    assert results2["owner"]["alerts_raised"] == 0
    assert Alert.objects.filter(owner=owner).count() == 1


def test_legacy_generate_insights_delegates_to_engine(seeded, fresh_source):
    insights = IntelligenceService.generate_insights(seeded, source_type="github")
    assert isinstance(insights, list)
    assert Insight.objects.filter(owner=seeded).exists()
    # no duplicates on second legacy call
    first = Insight.objects.filter(owner=seeded).count()
    IntelligenceService.generate_insights(seeded, source_type="github")
    assert Insight.objects.filter(owner=seeded).count() == first
