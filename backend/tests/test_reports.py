import pytest

from reports.exporters import export_markdown, export_pdf, export_xlsx
from reports.models import Report
from reports.services import generate_report


@pytest.mark.django_db
def test_generate_daily_report(seeded):
    result = generate_report(seeded, period="daily")
    assert result.status == "ok"
    report = Report.objects.filter(owner=seeded, period="daily").first()
    assert report is not None
    assert "Coding" in report.content


@pytest.mark.django_db
def test_exporters_return_bytes(seeded):
    generate_report(seeded, period="weekly")
    report = Report.objects.filter(owner=seeded, period="weekly").first()
    md, mt, fn = export_markdown(report)
    assert b"#" in md and mt == "text/markdown"
    pdf, mt2, _ = export_pdf(report)
    assert pdf.startswith(b"%PDF") and mt2 == "application/pdf"
    xlsx, mt3, _ = export_xlsx(report)
    assert xlsx.startswith(b"PK") and "spreadsheet" in mt3
