from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_REGULAR = "CompetitorAnalysisRegular"
FONT_BOLD = "CompetitorAnalysisBold"

FONT_REGULAR_CANDIDATES = [
    Path(settings.BASE_DIR) / "static" / "fonts" / "DejaVuSans.ttf",
    Path(settings.BASE_DIR) / "static" / "fonts" / "Arial.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]
FONT_BOLD_CANDIDATES = [
    Path(settings.BASE_DIR) / "static" / "fonts" / "DejaVuSans-Bold.ttf",
    Path(settings.BASE_DIR) / "static" / "fonts" / "Arial Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]

COLOR_PRIMARY = colors.HexColor("#0F766E")
COLOR_TEXT = colors.HexColor("#111827")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_HEAD = colors.HexColor("#ECFDF5")
COLOR_ALT = colors.HexColor("#F8FAFC")


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _ensure_fonts_registered() -> None:
    try:
        pdfmetrics.getFont(FONT_REGULAR)
        pdfmetrics.getFont(FONT_BOLD)
        return
    except KeyError:
        pass

    regular_path = _first_existing(FONT_REGULAR_CANDIDATES)
    if not regular_path:
        raise FileNotFoundError("Не найден шрифт для PDF с поддержкой кириллицы.")
    bold_path = _first_existing(FONT_BOLD_CANDIDATES) or regular_path
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular_path)))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold_path)))


def _styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    if "ca_title" not in styles:
        styles.add(
            ParagraphStyle(
                name="ca_title",
                parent=styles["Title"],
                fontName=FONT_BOLD,
                fontSize=18,
                leading=23,
                textColor=COLOR_PRIMARY,
                alignment=1,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_subtitle",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=10,
                leading=14,
                textColor=COLOR_TEXT,
                alignment=1,
                spaceAfter=3,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_h2",
                parent=styles["Heading2"],
                fontName=FONT_BOLD,
                fontSize=12,
                leading=16,
                textColor=COLOR_PRIMARY,
                spaceBefore=8,
                spaceAfter=5,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_body",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=9,
                leading=13,
                textColor=COLOR_TEXT,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_cell",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=8.3,
                leading=10.8,
                textColor=COLOR_TEXT,
                wordWrap="CJK",
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_cell_head",
                parent=styles["BodyText"],
                fontName=FONT_BOLD,
                fontSize=8.3,
                leading=10.8,
                textColor=COLOR_PRIMARY,
                wordWrap="CJK",
            )
        )
    return {
        "title": styles["ca_title"],
        "subtitle": styles["ca_subtitle"],
        "h2": styles["ca_h2"],
        "body": styles["ca_body"],
        "cell": styles["ca_cell"],
        "cell_head": styles["ca_cell_head"],
    }


def _sanitize_text(value: Any, fallback: str = "—") -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return fallback
    return "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)


def _escape_text(value: Any, fallback: str = "—") -> str:
    return _sanitize_text(value, fallback=fallback).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _p(text: Any, style_key: str, *, fallback: str = "—") -> Paragraph:
    return Paragraph(_escape_text(text, fallback=fallback), _styles()[style_key])


def _display_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if value in (None, ""):
        return "—"
    return str(value)


def _table(
    elements: list,
    *,
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    widths: list[float],
    rows_per_chunk: int = 24,
) -> None:
    elements.append(_p(title, "h2"))
    if not rows:
        rows = [["Данные отсутствуют"] + [""] * max(0, len(headers) - 1)]

    start = 0
    while start < len(rows):
        chunk = rows[start : start + rows_per_chunk]
        matrix = [[_p(item, "cell_head") for item in headers]]
        for row in chunk:
            matrix.append([_p(_display_value(item), "cell") for item in row])

        table = Table(matrix, colWidths=widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEAD),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_ALT]),
                    ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 7))
        start += rows_per_chunk
        if start < len(rows):
            elements.append(PageBreak())


def _safe_filename(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", ".") else "-" for ch in str(value or "").lower())
    return safe.strip("-.") or "site"


def build_competitor_analysis_pdf(*, analysis, payload: dict[str, Any]) -> tuple[bytes, str]:
    _ensure_fonts_registered()

    generated_at = timezone.localtime(analysis.finished_at or analysis.updated_at or timezone.now())
    site_name = _sanitize_text(getattr(analysis.site, "name", ""), fallback="Сайт")
    site_domain = _sanitize_text(payload.get("site_domain") or getattr(analysis.site, "domain", ""), fallback="—")
    items = [item for item in payload.get("items", []) if isinstance(item, dict)]
    competitors = [item for item in items if item.get("role") == "competitor"]
    filename = f"competitor-analysis-{_safe_filename(getattr(analysis.site, 'slug', '') or site_domain)}-{generated_at:%Y%m%d}.pdf"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Анализ конкурентов: {site_name}",
    )

    elements: list = [
        _p("Анализ конкурентов", "title"),
        _p(f"Сайт: {site_name}", "subtitle"),
        _p(f"Домен сайта: {site_domain}", "subtitle"),
        _p(f"Дата анализа: {generated_at:%d.%m.%Y %H:%M}", "subtitle"),
        Spacer(1, 10),
    ]

    _table(
        elements,
        title="Конкуренты",
        headers=["#", "Домен"],
        rows=[[idx, item.get("domain")] for idx, item in enumerate(competitors, start=1)],
        widths=[18 * mm, 158 * mm],
        rows_per_chunk=12,
    )
    elements.append(PageBreak())

    comparison_rows = []
    for row in payload.get("comparison", []):
        if not isinstance(row, dict):
            continue
        comparison_rows.append([row.get("metric"), *list(row.get("values") or [])])

    headers = ["Показатель"] + [item.get("label") or item.get("domain") or "Сайт" for item in items]
    first_width = 42 * mm
    rest_width = (176 * mm - first_width) / max(1, len(headers) - 1)
    _table(
        elements,
        title="Сводная сравнительная таблица",
        headers=headers,
        rows=comparison_rows,
        widths=[first_width] + [rest_width] * (len(headers) - 1),
        rows_per_chunk=18,
    )
    elements.append(PageBreak())

    detail_rows = []
    for item in items:
        detail_rows.append(
            [
                item.get("label"),
                item.get("domain"),
                item.get("http_status"),
                item.get("seo_score"),
                item.get("title"),
                item.get("description"),
                item.get("h1"),
                item.get("h2_count"),
                item.get("robots_txt"),
                item.get("sitemap_xml"),
                item.get("canonical"),
                item.get("https"),
                item.get("errors_count"),
            ]
        )
    _table(
        elements,
        title="Подробное сравнение",
        headers=[
            "Тип",
            "Домен",
            "HTTP",
            "Score",
            "Title",
            "Description",
            "H1",
            "H2",
            "Robots",
            "Sitemap",
            "Canonical",
            "HTTPS",
            "Ошибки",
        ],
        rows=detail_rows,
        widths=[18 * mm, 25 * mm, 13 * mm, 14 * mm, 24 * mm, 24 * mm, 20 * mm, 10 * mm, 12 * mm, 12 * mm, 24 * mm, 12 * mm, 12 * mm],
        rows_per_chunk=8,
    )

    recommendations = payload.get("recommendations") if isinstance(payload.get("recommendations"), dict) else {}
    for title, key in (("Критично", "critical"), ("Важно", "important"), ("Желательно", "desired")):
        rows = [[idx, item] for idx, item in enumerate(recommendations.get(key) or [], start=1)]
        _table(
            elements,
            title=f"Рекомендации: {title}",
            headers=["#", "Что сделать"],
            rows=rows,
            widths=[12 * mm, 164 * mm],
            rows_per_chunk=20,
        )

    plan_rows = [[idx, item] for idx, item in enumerate(payload.get("improvement_plan") or [], start=1)]
    _table(
        elements,
        title="Итоговый план улучшений",
        headers=["#", "Шаг"],
        rows=plan_rows,
        widths=[12 * mm, 164 * mm],
        rows_per_chunk=20,
    )

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf, filename
