"""Report exporters: Markdown, HTML, PDF (reportlab), XLSX (openpyxl), DOCX.

Each returns (content_bytes, media_type, filename). PDF uses a lightweight
markdown→flowable parser that covers the constructs the agent emits
(headings, bullets, bold) — enough for clean executive reports.
"""
import io

from core.utils import slugify


def _lines(report) -> list[str]:
    return report.content.splitlines()


# ── Markdown / HTML ────────────────────────────────────────────────────────
def export_markdown(report) -> tuple[bytes, str, str]:
    return report.content.encode("utf-8"), "text/markdown", f"{slugify(report.title)}.md"


def export_html(report) -> tuple[bytes, str, str]:
    html = report.html or f"<pre>{report.content}</pre>"
    styled = (
        "<html><head><meta charset='utf-8'><style>"
        "body{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;color:#1a1a2e}"
        "h1,h2{color:#0f3460}li{margin:.25rem 0}</style></head>"
        f"<body>{html}</body></html>"
    )
    return styled.encode("utf-8"), "text/html", f"{slugify(report.title)}.html"


# ── PDF (reportlab) ────────────────────────────────────────────────────────
def export_pdf(report) -> tuple[bytes, str, str]:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm, title=report.title
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#0f3460"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#0f3460"))
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.5, leading=15)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=10, bulletIndent=0)

    story: list = []
    for line in _lines(report):
        text = line.strip()
        if not text:
            story.append(Spacer(1, 6))
        elif text.startswith("# "):
            story.append(Paragraph(text[2:], h1))
        elif text.startswith("## "):
            story.append(Paragraph(text[3:], h2))
        elif text.startswith("- "):
            story.append(Paragraph(text[2:], bullet, bulletText="•"))
        elif text.startswith("*"):
            story.append(Paragraph(text, body))
        else:
            story.append(Paragraph(text, body))

    doc.build(story)
    return buffer.getvalue(), "application/pdf", f"{slugify(report.title)}.pdf"


# ── XLSX (openpyxl) ────────────────────────────────────────────────────────
def export_xlsx(report) -> tuple[bytes, str, str]:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = report.period
    header = ["Metric", "Value"]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="0F3460")
        cell.font = Font(bold=True, color="FFFFFF")

    # Flatten the report data into rows.
    data = report.data or {}
    def walk(prefix, mapping):
        for key, value in mapping.items():
            if isinstance(value, (dict, list)):
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    ws.append([f"{prefix}{key} (count)", len(value)])
                    continue
                walk(f"{prefix}{key} > ", value)
            else:
                ws.append([f"{prefix}{key}".strip(" >"), value])

    walk("", data)
    ws.append([])
    ws.append(["Report title", report.title])
    ws.append(["Period", f"{report.period_start} → {report.period_end}"])
    for col in ("A", "B"):
        ws.column_dimensions[col].width = 42
    wb.save(buffer := io.BytesIO())
    return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", f"{slugify(report.title)}.xlsx"


# ── DOCX (python-docx) ─────────────────────────────────────────────────────
def export_docx(report) -> tuple[bytes, str, str]:
    from docx import Document
    from docx.shared import Pt

    document = Document()
    document.add_heading(report.title, level=0)
    for line in _lines(report):
        text = line.strip()
        if not text:
            continue
        if text.startswith("# "):
            document.add_heading(text[2:], level=1)
        elif text.startswith("## "):
            document.add_heading(text[3:], level=2)
        elif text.startswith("- "):
            document.add_paragraph(text[2:], style="List Bullet")
        else:
            p = document.add_paragraph(text)
            p.style.font.size = Pt(10.5)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", f"{slugify(report.title)}.docx"


EXPORTERS = {
    "md": export_markdown,
    "html": export_html,
    "pdf": export_pdf,
    "xlsx": export_xlsx,
    "docx": export_docx,
}
