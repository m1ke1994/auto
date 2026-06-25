from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from seo_audit.services.text_encoding import has_mojibake, log_text_diagnostics

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
COLOR_PRIMARY_DARK = colors.HexColor("#115E59")
COLOR_TEXT = colors.HexColor("#111827")
COLOR_MUTED = colors.HexColor("#475569")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_HEAD = colors.HexColor("#E6F7F4")
COLOR_ALT = colors.HexColor("#F8FAFC")
COLOR_SOFT = colors.HexColor("#F1F5F9")
COLOR_DANGER = colors.HexColor("#B91C1C")
COLOR_WARNING = colors.HexColor("#B45309")
COLOR_SUCCESS = colors.HexColor("#047857")

logger = logging.getLogger(__name__)


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
    pdfmetrics.registerFontFamily("CompetitorAnalysis", normal=FONT_REGULAR, bold=FONT_BOLD)


def _styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    if "ca_title" not in styles:
        styles.add(
            ParagraphStyle(
                name="ca_title",
                parent=styles["Title"],
                fontName=FONT_BOLD,
                fontSize=28,
                leading=34,
                textColor=COLOR_PRIMARY_DARK,
                alignment=TA_CENTER,
                spaceAfter=8,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_subtitle",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=11,
                leading=16,
                textColor=COLOR_MUTED,
                alignment=TA_CENTER,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_h2",
                parent=styles["Heading2"],
                fontName=FONT_BOLD,
                fontSize=16,
                leading=21,
                textColor=COLOR_PRIMARY_DARK,
                spaceBefore=6,
                spaceAfter=8,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_h3",
                parent=styles["Heading3"],
                fontName=FONT_BOLD,
                fontSize=12,
                leading=16,
                textColor=COLOR_TEXT,
                spaceBefore=6,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_body",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=9.5,
                leading=14,
                textColor=COLOR_TEXT,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_muted",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=8.5,
                leading=12,
                textColor=COLOR_MUTED,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_cell",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=8.4,
                leading=11.2,
                textColor=COLOR_TEXT,
                wordWrap="CJK",
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_cell_head",
                parent=styles["BodyText"],
                fontName=FONT_BOLD,
                fontSize=8.4,
                leading=11.2,
                textColor=COLOR_PRIMARY_DARK,
                wordWrap="CJK",
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_card_label",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=8.2,
                leading=10,
                textColor=COLOR_MUTED,
                alignment=TA_CENTER,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ca_card_value",
                parent=styles["BodyText"],
                fontName=FONT_BOLD,
                fontSize=16,
                leading=20,
                textColor=COLOR_PRIMARY_DARK,
                alignment=TA_CENTER,
            )
        )
    return {
        "title": styles["ca_title"],
        "subtitle": styles["ca_subtitle"],
        "h2": styles["ca_h2"],
        "h3": styles["ca_h3"],
        "body": styles["ca_body"],
        "muted": styles["ca_muted"],
        "cell": styles["ca_cell"],
        "cell_head": styles["ca_cell_head"],
        "card_label": styles["ca_card_label"],
        "card_value": styles["ca_card_value"],
    }


def _sanitize_text(value: Any, fallback: str = "—") -> str:
    text = ("" if value is None else str(value)).replace("�", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return fallback
    if has_mojibake(text):
        logger.warning("competitor_analysis.pdf mojibake before paragraph sample=%r", text[:180])
    return "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)


def _escape_text(value: Any, fallback: str = "—") -> str:
    return (
        _sanitize_text(value, fallback=fallback)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _p(text: Any, style_key: str, *, fallback: str = "—") -> Paragraph:
    return Paragraph(_escape_text(text, fallback=fallback), _styles()[style_key])


def _short(value: Any, *, limit: int = 120, fallback: str = "—") -> str:
    text = " ".join(_sanitize_text(value, fallback=fallback).split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _yes_no(value: Any) -> str:
    return "Да" if bool(value) else "Нет"


def _present(value: Any) -> str:
    return "Есть" if str(value or "").strip() else "Нет"


def _first_item(items: list[dict[str, Any]], role: str) -> dict[str, Any]:
    return next((item for item in items if item.get("role") == role), {})


def _safe_filename(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", ".") else "-" for ch in str(value or "").lower())
    return safe.strip("-.") or "site"


def _log_pdf_table_rows(table_name: str, rows: list[list[Any]]) -> None:
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            log_text_diagnostics(
                logger,
                "competitor_analysis.pdf.table_cell",
                value,
                table=table_name,
                row=row_index,
                column=column_index,
            )


def _log_pdf_payload_diagnostics(payload: dict[str, Any], own: dict[str, Any], competitor: dict[str, Any]) -> None:
    for role, item in (("own", own), ("competitor", competitor)):
        for field in ("title", "description", "h1"):
            log_text_diagnostics(
                logger,
                "competitor_analysis.pdf.payload",
                item.get(field),
                role=role,
                field=field,
                domain=item.get("domain"),
            )

    recommendations = payload.get("recommendations") if isinstance(payload.get("recommendations"), dict) else {}
    for group, rows in recommendations.items():
        for index, row in enumerate((rows or [])[:5]):
            log_text_diagnostics(
                logger,
                "competitor_analysis.pdf.recommendation",
                row,
                group=group,
                index=index,
            )


def _draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 8)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawString(doc.leftMargin, 10 * mm, "Анализ конкурентов")
    canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Стр. {doc.page}")
    canvas.restoreState()


def _add_card_table(elements: list, cards: list[tuple[str, str]]) -> None:
    if not cards:
        return

    row = []
    for label, value in cards:
        row.append([_p(value, "card_value"), _p(label, "card_label")])

    table = Table([row], colWidths=[47 * mm] * len(row))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_SOFT),
                ("BOX", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 8))


def _section(elements: list, title: str) -> None:
    elements.append(_p(title, "h2"))


def _paragraphs(elements: list, rows: list[str]) -> None:
    for row in rows:
        if row:
            elements.append(_p(row, "body"))


def _bullet_list(elements: list, rows: list[str], *, empty_text: str = "Данные отсутствуют.") -> None:
    clean_rows = [_sanitize_text(row) for row in rows if str(row or "").strip()]
    if not clean_rows:
        clean_rows = [empty_text]
    for row in clean_rows:
        elements.append(_p(f"• {row}", "body"))


def _numbered_list(elements: list, rows: list[str], *, empty_text: str = "Данные отсутствуют.") -> None:
    clean_rows = [_sanitize_text(row) for row in rows if str(row or "").strip()]
    if not clean_rows:
        clean_rows = [empty_text]
    for index, row in enumerate(clean_rows, start=1):
        elements.append(_p(f"{index}. {row}", "body"))


def _summary_findings(own: dict[str, Any], competitor: dict[str, Any]) -> list[str]:
    own_score = _safe_int(own.get("seo_score"))
    competitor_score = _safe_int(competitor.get("seo_score"))
    own_errors = _safe_int(own.get("errors_count"))
    competitor_errors = _safe_int(competitor.get("errors_count"))

    rows = [
        f"Ваш сайт набрал {own_score} баллов, сайт конкурента — {competitor_score} баллов.",
    ]
    if own_score > competitor_score:
        rows.append("По суммарному SEO score ваш сайт сейчас сильнее конкурента.")
    elif competitor_score > own_score:
        rows.append("Конкурент опережает ваш сайт по суммарному SEO score.")
    else:
        rows.append("По суммарному SEO score сайты находятся примерно на одном уровне.")

    if own_errors > competitor_errors:
        rows.append("Главное отставание связано с большим количеством SEO-ошибок на вашем сайте.")
    elif competitor_errors > own_errors:
        rows.append("У конкурента больше SEO-ошибок, но отдельные технические показатели всё равно стоит проверить.")
    else:
        rows.append("Количество найденных SEO-ошибок у сайтов сопоставимо.")

    if not own.get("h1"):
        rows.append("На вашем сайте нужно добавить понятный H1 на главную страницу.")
    elif not own.get("description"):
        rows.append("На вашем сайте стоит улучшить meta description для поисковой выдачи.")
    elif not own.get("sitemap_xml"):
        rows.append("На вашем сайте стоит добавить sitemap.xml для более понятной индексации.")
    return rows[:4]


def _competitor_advantages(own: dict[str, Any], competitor: dict[str, Any]) -> list[str]:
    rows = []
    if _safe_int(competitor.get("seo_score")) > _safe_int(own.get("seo_score")):
        rows.append("Выше SEO score.")
    if _safe_int(competitor.get("errors_count")) < _safe_int(own.get("errors_count")):
        rows.append("Меньше SEO-ошибок.")
    if competitor.get("title") and not own.get("title"):
        rows.append("Заполнен Title на главной странице.")
    if competitor.get("description") and not own.get("description"):
        rows.append("Заполнен meta description.")
    if competitor.get("h1") and not own.get("h1"):
        rows.append("Есть главный заголовок H1.")
    if _safe_int(competitor.get("h2_count")) > _safe_int(own.get("h2_count")):
        rows.append("Лучше выражена структура подзаголовков H2.")
    if competitor.get("robots_txt") and not own.get("robots_txt"):
        rows.append("Найден robots.txt.")
    if competitor.get("sitemap_xml") and not own.get("sitemap_xml"):
        rows.append("Найден sitemap.xml.")
    if competitor.get("https") and not own.get("https"):
        rows.append("Подтверждён HTTPS.")
    return rows or ["По ключевым проверенным SEO-показателям конкурент не выглядит сильнее вашего сайта."]


def _comparison_table(elements: list, own: dict[str, Any], competitor: dict[str, Any]) -> None:
    rows = [
        ["SEO score", _safe_int(own.get("seo_score")), _safe_int(competitor.get("seo_score"))],
        ["Title", _present(own.get("title")), _present(competitor.get("title"))],
        ["Description", _present(own.get("description")), _present(competitor.get("description"))],
        ["H1", _present(own.get("h1")), _present(competitor.get("h1"))],
        ["H2", _safe_int(own.get("h2_count")), _safe_int(competitor.get("h2_count"))],
        ["robots.txt", _yes_no(own.get("robots_txt")), _yes_no(competitor.get("robots_txt"))],
        ["sitemap.xml", _yes_no(own.get("sitemap_xml")), _yes_no(competitor.get("sitemap_xml"))],
        ["HTTPS", _yes_no(own.get("https")), _yes_no(competitor.get("https"))],
        ["Количество ошибок", _safe_int(own.get("errors_count")), _safe_int(competitor.get("errors_count"))],
    ]
    _log_pdf_table_rows("comparison", rows)
    matrix = [[_p("Показатель", "cell_head"), _p("Ваш сайт", "cell_head"), _p("Конкурент", "cell_head")]]
    for row in rows:
        matrix.append([_p(item, "cell") for item in row])

    table = Table(matrix, colWidths=[58 * mm, 50 * mm, 50 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEAD),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.35, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 7))


def _metadata_block(elements: list, own: dict[str, Any], competitor: dict[str, Any]) -> None:
    rows = [
        ["Title вашего сайта", _short(own.get("title"), limit=160)],
        ["Title конкурента", _short(competitor.get("title"), limit=160)],
        ["Description вашего сайта", _short(own.get("description"), limit=220)],
        ["Description конкурента", _short(competitor.get("description"), limit=220)],
    ]
    _log_pdf_table_rows("metadata", rows)
    matrix = [[_p("Поле", "cell_head"), _p("Значение", "cell_head")]]
    for row in rows:
        matrix.append([_p(item, "cell") for item in row])
    table = Table(matrix, colWidths=[47 * mm, 111 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEAD),
                ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)


def _issue_importance(issue_type: str) -> str:
    issue = str(issue_type or "").lower()
    if "title" in issue:
        return "Title влияет на вид страницы в поисковой выдаче и помогает понять тему страницы."
    if "description" in issue:
        return "Description помогает пользователю выбрать ваш сайт в поисковой выдаче."
    if "h1" in issue or "heading" in issue:
        return "Заголовки помогают поисковым системам и посетителям быстрее понять структуру страницы."
    if "robots" in issue or "sitemap" in issue or "canonical" in issue or "index" in issue:
        return "Ошибки индексации мешают поисковым системам корректно находить и понимать страницы."
    if "slow" in issue or "size" in issue or "payload" in issue or "js" in issue or "css" in issue:
        return "Скорость и вес страницы влияют на удобство пользователя и качество поискового продвижения."
    if "image" in issue:
        return "Описания изображений помогают поиску и улучшают доступность сайта."
    return "Проблема снижает качество страницы для пользователей или поисковых систем."


def _issue_card(issue: dict[str, Any]) -> KeepTogether:
    title = issue.get("title") or issue.get("type") or "SEO-проблема"
    page_url = _short(issue.get("page_url"), limit=120, fallback="")
    page_suffix = f" Страница: {page_url}" if page_url else ""
    blocks = [
        _p(f"Проблема: {_sanitize_text(title)}{page_suffix}", "body"),
        _p(f"Почему важно: {_issue_importance(str(issue.get('type') or ''))}", "body"),
        _p(f"Что сделать: {_sanitize_text(issue.get('recommendation'), fallback='Проверьте страницу и устраните проблему.')}", "body"),
        Spacer(1, 4),
    ]
    return KeepTogether(blocks)


def _issue_section(elements: list, own: dict[str, Any]) -> None:
    issues = [item for item in own.get("issues") or [] if isinstance(item, dict)]
    grouped = {
        "high": [],
        "medium": [],
        "low": [],
    }
    for issue in issues:
        severity = str(issue.get("severity") or "").lower()
        if severity in grouped:
            grouped[severity].append(issue)

    for title, key in (
        ("Критичные ошибки", "high"),
        ("Важные ошибки", "medium"),
        ("Предупреждения", "low"),
    ):
        elements.append(_p(title, "h3"))
        rows = grouped[key]
        if not rows:
            elements.append(_p("В этой группе ошибок не найдено.", "body"))
            continue
        for issue in rows[:8]:
            elements.append(_issue_card(issue))
        if len(rows) > 8:
            elements.append(_p(f"Ещё {len(rows) - 8} ошибок этой группы есть в полном SEO-аудите.", "muted"))


def _recommendation_sections(elements: list, recommendations: dict[str, list[str]]) -> None:
    for title, key in (
        ("Сделать в первую очередь", "critical"),
        ("Сделать далее", "important"),
        ("Желательно улучшить", "desired"),
    ):
        elements.append(_p(title, "h3"))
        _bullet_list(elements, recommendations.get(key) or [], empty_text="Отдельных рекомендаций в этой группе нет.")


def build_competitor_analysis_pdf(*, analysis, payload: dict[str, Any]) -> tuple[bytes, str]:
    _ensure_fonts_registered()

    generated_at = timezone.localtime(analysis.finished_at or analysis.updated_at or timezone.now())
    site_name = _sanitize_text(getattr(analysis.site, "name", ""), fallback="Сайт")
    user_domain = _sanitize_text(
        payload.get("user_domain") or payload.get("site_domain") or getattr(analysis, "user_domain", ""),
        fallback="—",
    )
    competitor_domain = _sanitize_text(
        payload.get("competitor_domain") or getattr(analysis, "competitor_domain", ""),
        fallback="—",
    )
    items = [item for item in payload.get("items", []) if isinstance(item, dict)]
    own = _first_item(items, "own")
    competitor = _first_item(items, "competitor")
    recommendations = payload.get("recommendations") if isinstance(payload.get("recommendations"), dict) else {}
    _log_pdf_payload_diagnostics(payload, own, competitor)
    filename = f"competitor-analysis-{_safe_filename(user_domain)}-{generated_at:%Y%m%d}.pdf"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title=f"Анализ конкурентов: {site_name}",
    )

    elements: list = [
        Spacer(1, 28),
        _p("Анализ конкурентов", "title"),
        _p("Отчёт показывает SEO-состояние вашего сайта в сравнении с конкурентом и даёт рекомендации по улучшению.", "subtitle"),
        Spacer(1, 16),
    ]
    _add_card_table(
        elements,
        [
            ("Ваш сайт", user_domain),
            ("Конкурент", competitor_domain),
            ("Дата анализа", f"{generated_at:%d.%m.%Y}"),
        ],
    )
    _paragraphs(
        elements,
        [
            f"Проект: {site_name}.",
            "Цель отчёта — быстро показать, где ваш сайт уступает конкуренту и какие действия дадут наибольший эффект.",
        ],
    )
    elements.append(PageBreak())

    _section(elements, "Краткое резюме")
    _add_card_table(
        elements,
        [
            ("SEO score вашего сайта", str(_safe_int(own.get("seo_score")))),
            ("SEO score конкурента", str(_safe_int(competitor.get("seo_score")))),
            ("Ошибок на вашем сайте", str(_safe_int(own.get("errors_count")))),
        ],
    )
    _bullet_list(elements, _summary_findings(own, competitor))

    elements.append(PageBreak())
    _section(elements, "Ошибки сайта пользователя")
    _issue_section(elements, own)

    elements.append(PageBreak())
    _section(elements, "Сравнение с конкурентом")
    _comparison_table(elements, own, competitor)
    elements.append(_p("Полные title и description вынесены отдельно, чтобы сравнительная таблица оставалась читаемой.", "muted"))
    elements.append(Spacer(1, 5))
    _metadata_block(elements, own, competitor)

    elements.append(PageBreak())
    _section(elements, "Что лучше у конкурента")
    _bullet_list(elements, _competitor_advantages(own, competitor))

    _section(elements, "Рекомендации")
    _recommendation_sections(elements, recommendations)

    elements.append(PageBreak())
    _section(elements, "Итоговый план")
    _numbered_list(elements, payload.get("improvement_plan") or [])
    elements.append(Spacer(1, 8))
    elements.append(_p("После внедрения изменений повторите анализ, чтобы увидеть динамику и проверить, ушли ли критичные ошибки.", "body"))

    doc.build(elements, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf, filename
