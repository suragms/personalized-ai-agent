"""Provenance: every generated artifact must declare what actually produced it.

REAL_AI_PROVIDER / MOCK_PROVIDER / DETERMINISTIC_TEMPLATE — never present
template or mock output as real AI output (and vice versa).
"""
import pytest

from ai.routing import PROVENANCE_MOCK, PROVENANCE_REAL, PROVENANCE_TEMPLATE
from ai.services import generate_prose_detailed


def test_without_owner_output_is_template():
    text, provenance = generate_prose_detailed(
        "system", "user", fallback="FALLBACK", owner=None
    )
    assert text == "FALLBACK"
    assert provenance == PROVENANCE_TEMPLATE
    assert provenance != PROVENANCE_REAL


@pytest.mark.django_db
def test_mock_provider_is_reported_as_mock(owner):
    markdown = "# Title\n- point one"
    text, provenance = generate_prose_detailed(
        "Summarize.", markdown, fallback="FALLBACK", owner=owner
    )
    assert provenance == PROVENANCE_MOCK
    # The deterministic mock passes formatted markdown through unchanged.
    assert text == markdown


@pytest.mark.django_db
def test_skip_mock_keeps_curated_fallback(owner):
    text, provenance = generate_prose_detailed(
        "system", "plain paragraph without structure", fallback="CURATED",
        owner=owner, skip_mock=True,
    )
    assert text == "CURATED"
    assert provenance == PROVENANCE_TEMPLATE


@pytest.mark.django_db
def test_report_persists_provenance(owner):
    from reports.models import Report
    from reports.services import generate_report

    result = generate_report(owner, period="daily")
    report = Report.objects.get(owner=owner, period="daily")

    assert report.provenance in (PROVENANCE_MOCK, PROVENANCE_REAL, PROVENANCE_TEMPLATE)
    assert result.data["provenance"] == report.provenance
    # In the test environment there are no provider connections: mock serves it.
    assert report.provenance == PROVENANCE_MOCK


@pytest.mark.django_db
def test_briefing_persists_provenance(owner):
    from productivity.models import Briefing
    from productivity.services import generate_eod, generate_morning

    morning = generate_morning(owner)
    eod = generate_eod(owner)

    assert morning.provenance == PROVENANCE_MOCK
    assert eod.provenance == PROVENANCE_MOCK
    assert Briefing.objects.filter(owner=owner, provenance=PROVENANCE_MOCK).count() == 2


@pytest.mark.django_db
def test_provenance_is_serialized_to_the_api(auth_client, owner):
    from reports.services import generate_report

    generate_report(owner, period="daily")
    resp = auth_client.get("/api/reports/")
    assert resp.status_code == 200
    results = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert results, "expected at least one report"
    assert results[0]["provenance"] == PROVENANCE_MOCK
