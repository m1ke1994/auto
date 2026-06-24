from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.security import DomainValidationError, normalize_public_domain, validate_public_analysis_domain
from competitor_analysis.services.pdf_report import build_competitor_analysis_pdf
from competitor_analysis.services.snapshot import collect_domain_snapshot
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from seo_audit.services.crawler import AuditCancelledError, crawl_site_audit
from seo_audit.services.messages import get_issue_title
from seo_audit.services.scoring import recalculate_audit_score
from seo_audit.services.text_encoding import has_mojibake, repair_mojibake

logger = logging.getLogger(__name__)


class AnalysisCanceled(Exception):
    pass


def _safe_short_text(value: Any, *, limit: int = 220) -> str:
    text = " ".join(repair_mojibake(value).split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _issue_counts(audit: SiteSEOAudit | None) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    if audit is None:
        return counts
    for severity in SEOIssue.objects.filter(page__audit=audit).values_list("severity", flat=True):
        if severity in counts:
            counts[severity] += 1
    return counts


def _issue_rows(audit: SiteSEOAudit | None, *, limit: int = 40) -> list[dict[str, str]]:
    if audit is None:
        return []
    rows = []
    qs = SEOIssue.objects.filter(page__audit=audit).select_related("page").order_by("severity", "id")
    for issue in list(qs[:limit]):
        rows.append(
            {
                "type": issue.issue_type,
                "title": get_issue_title(issue.issue_type),
                "severity": issue.severity,
                "page_url": repair_mojibake(getattr(issue.page, "url", "")),
                "recommendation": repair_mojibake(issue.recommendation),
            }
        )
    return rows


def _home_page(audit: SiteSEOAudit | None, domain: str) -> SEOPage | None:
    if audit is None:
        return None
    candidates = [f"https://{domain}/", f"http://{domain}/"]
    for url in candidates:
        page = audit.pages.filter(url=url).first()
        if page is not None:
            return page
    return audit.pages.order_by("id").first()


def _run_existing_seo_audit(*, client, domain: str, stop_check=None) -> tuple[SiteSEOAudit, str]:
    audit = SiteSEOAudit.objects.create(
        client=client,
        domain=domain,
        status=SiteSEOAudit.Status.RUNNING,
        finished_at=None,
    )
    error = ""
    max_pages = int(getattr(settings, "COMPETITOR_ANALYSIS_MAX_PAGES", 20) or 20)

    try:
        crawl_site_audit(audit, max_pages=max_pages, stop_check=stop_check)
        recalculate_audit_score(audit)
        audit.status = SiteSEOAudit.Status.DONE
        audit.finished_at = timezone.now()
        audit.save(update_fields=["status", "finished_at"])
    except AuditCancelledError as exc:
        error = str(exc) or "SEO-аудит был остановлен."
        audit.status = SiteSEOAudit.Status.STOPPED
        audit.finished_at = timezone.now()
        audit.save(update_fields=["status", "finished_at"])
    except Exception as exc:
        logger.exception("competitor_analysis SEO audit failed domain=%s", domain)
        error = str(exc) or "SEO-аудит завершился ошибкой."
        audit.status = SiteSEOAudit.Status.ERROR
        audit.finished_at = timezone.now()
        audit.save(update_fields=["status", "finished_at"])

    return audit, error


def _build_domain_result(
    *,
    role: str,
    label: str,
    domain: str,
    audit: SiteSEOAudit | None,
    audit_error: str,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    page = _home_page(audit, domain)
    counts = _issue_counts(audit)
    errors_count = int(counts["high"] + counts["medium"] + counts["low"])
    snapshot_error = str(snapshot.get("error") or "")
    error = audit_error or snapshot_error

    return {
        "role": role,
        "label": label,
        "domain": domain,
        "audit_id": getattr(audit, "id", None),
        "audit_status": getattr(audit, "status", ""),
        "http_status": int(snapshot.get("status_code") or getattr(page, "status_code", 0) or 0),
        "https": bool(snapshot.get("https")),
        "title": _safe_short_text(snapshot.get("title") or getattr(page, "title", "")),
        "description": _safe_short_text(snapshot.get("description") or getattr(page, "description", "")),
        "h1": _safe_short_text(snapshot.get("h1") or getattr(page, "h1", "")),
        "h1_count": int(snapshot.get("h1_count") or getattr(page, "h1_count", 0) or 0),
        "h2_count": int(snapshot.get("h2_count") or 0),
        "canonical": _safe_short_text(snapshot.get("canonical") or getattr(page, "canonical_url", "")),
        "robots_txt": bool(getattr(audit, "has_robots_txt", False)),
        "sitemap_xml": bool(getattr(audit, "has_sitemap_xml", False)),
        "lang": _safe_short_text(snapshot.get("lang")),
        "viewport": bool(snapshot.get("viewport")),
        "open_graph": bool(snapshot.get("open_graph")),
        "internal_links_count": int(snapshot.get("internal_links_count") or 0),
        "external_links_count": int(snapshot.get("external_links_count") or 0),
        "html_size_bytes": int(snapshot.get("html_size_bytes") or getattr(page, "html_size_bytes", 0) or 0),
        "seo_score": int(getattr(audit, "seo_score", 0) or 0),
        "errors_count": errors_count,
        "high_issues": int(counts["high"]),
        "medium_issues": int(counts["medium"]),
        "low_issues": int(counts["low"]),
        "issues": _issue_rows(audit),
        "error": _safe_short_text(error, limit=500),
    }


def _display_metric(value: Any, *, key: str = "") -> str:
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if key in {"title", "description", "h1", "canonical"}:
        return "Есть" if str(value or "").strip() else "Нет"
    if value in (None, ""):
        return "—"
    return str(value)


def _build_comparison(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metric_map = [
        ("SEO score", "seo_score"),
        ("Title", "title"),
        ("Description", "description"),
        ("H1", "h1"),
        ("H2", "h2_count"),
        ("robots.txt", "robots_txt"),
        ("sitemap.xml", "sitemap_xml"),
        ("Canonical", "canonical"),
        ("HTTPS", "https"),
        ("Ошибок", "errors_count"),
    ]
    rows = []
    for title, key in metric_map:
        rows.append(
            {
                "metric": title,
                "key": key,
                "values": [_display_metric(item.get(key), key=key) for item in items],
            }
        )
    return rows


def _competitors(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item.get("role") == "competitor"]


def _build_recommendations(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    own = next((item for item in items if item.get("role") == "own"), None)
    competitors = _competitors(items)
    recommendations = {"critical": [], "important": [], "desired": []}
    if not own:
        recommendations["critical"].append("Не удалось получить данные по вашему сайту. Проверьте домен сайта.")
        return recommendations

    if own.get("error"):
        recommendations["critical"].append(f"Ваш сайт сейчас недоступен для проверки: {own['error']}")
    if int(own.get("http_status") or 0) and int(own.get("http_status") or 0) != 200:
        recommendations["critical"].append("Проверьте главную страницу: она должна отвечать HTTP 200.")
    if competitors and not own.get("https") and any(item.get("https") for item in competitors):
        recommendations["critical"].append("У конкурентов работает HTTPS, а у вашего сайта он не подтверждён. Настройте HTTPS.")
    if not own.get("h1"):
        recommendations["critical"].append("Добавьте один понятный H1 на главную страницу.")

    best_score = max([int(item.get("seo_score") or 0) for item in competitors] or [0])
    if best_score and int(own.get("seo_score") or 0) < best_score:
        recommendations["important"].append(
            f"Ваш SEO score ниже лучшего конкурента: {own.get('seo_score', 0)} против {best_score}."
        )
    if not own.get("title"):
        recommendations["important"].append("Добавьте title на главную страницу.")
    if not own.get("description"):
        recommendations["important"].append("Добавьте meta description на главную страницу.")
    if competitors and not own.get("sitemap_xml") and any(item.get("sitemap_xml") for item in competitors):
        recommendations["important"].append("У конкурентов найден sitemap.xml, а у вашего сайта он отсутствует.")
    if competitors and not own.get("robots_txt") and any(item.get("robots_txt") for item in competitors):
        recommendations["important"].append("Добавьте robots.txt и укажите в нём ссылку на sitemap.xml.")
    if competitors and not own.get("canonical") and any(item.get("canonical") for item in competitors):
        recommendations["important"].append("Добавьте canonical URL на главную страницу.")
    if competitors and int(own.get("errors_count") or 0) > min(int(item.get("errors_count") or 0) for item in competitors):
        recommendations["important"].append("У вашего сайта больше SEO-ошибок, чем у части конкурентов. Начните с критичных ошибок.")

    max_h2 = max([int(item.get("h2_count") or 0) for item in competitors] or [0])
    if max_h2 and int(own.get("h2_count") or 0) < max_h2:
        recommendations["desired"].append("Ваш сайт уступает конкурентам по структуре подзаголовков H2.")
    if not own.get("open_graph"):
        recommendations["desired"].append("Добавьте Open Graph-теги для корректного отображения ссылок в соцсетях и мессенджерах.")
    if not own.get("viewport"):
        recommendations["desired"].append("Добавьте meta viewport для корректной мобильной выдачи.")
    if int(own.get("internal_links_count") or 0) < 3:
        recommendations["desired"].append("Усилите внутреннюю перелинковку с главной страницы.")

    for key in recommendations:
        seen = set()
        unique_items = []
        for item in recommendations[key]:
            if item in seen:
                continue
            seen.add(item)
            unique_items.append(item)
        recommendations[key] = unique_items[:8]

    return recommendations


def _build_improvement_plan(recommendations: dict[str, list[str]]) -> list[str]:
    plan = []
    for key in ("critical", "important", "desired"):
        plan.extend(recommendations.get(key) or [])
    if not plan:
        return ["Поддерживайте текущие SEO-показатели и регулярно повторяйте анализ конкурентов."]
    return plan[:6]


def _repair_report_payload_text(payload: dict[str, Any]) -> dict[str, Any]:
    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        domain = item.get("domain") or ""
        for key in ("title", "description", "h1", "canonical", "lang", "error"):
            original = item.get(key)
            fixed = repair_mojibake(original)
            item[key] = fixed
            if has_mojibake(fixed):
                logger.warning("competitor_analysis mojibake remains domain=%s field=%s value=%r", domain, key, fixed[:160])
        for issue in item.get("issues") or []:
            if not isinstance(issue, dict):
                continue
            for key in ("title", "page_url", "recommendation"):
                issue[key] = repair_mojibake(issue.get(key))

    recommendations = payload.get("recommendations")
    if isinstance(recommendations, dict):
        for key, rows in recommendations.items():
            if isinstance(rows, list):
                recommendations[key] = [repair_mojibake(row) for row in rows]
    payload["improvement_plan"] = [repair_mojibake(row) for row in payload.get("improvement_plan") or []]
    return payload


def _analysis_domains(analysis: CompetitorAnalysis) -> tuple[str, str]:
    raw_user_domain = analysis.user_domain or getattr(analysis.site, "domain", "")
    user_domain = normalize_public_domain(raw_user_domain, resolve_dns=False)

    competitors = analysis.competitors if isinstance(analysis.competitors, list) else []
    raw_competitor_domain = analysis.competitor_domain or (competitors[0] if competitors else "")
    competitor_domain = normalize_public_domain(raw_competitor_domain, resolve_dns=False)
    return user_domain, competitor_domain


def run_competitor_analysis(analysis: CompetitorAnalysis) -> CompetitorAnalysis:
    analysis = CompetitorAnalysis.objects.select_related("site", "client").get(id=analysis.id)

    def _check_canceled() -> None:
        analysis.refresh_from_db(fields=["status"])
        if analysis.status == CompetitorAnalysis.Status.CANCELED:
            raise AnalysisCanceled("Анализ остановлен.")

    def _stop_requested() -> bool:
        analysis.refresh_from_db(fields=["status"])
        return analysis.status == CompetitorAnalysis.Status.CANCELED

    _check_canceled()
    user_domain, competitor_domain = _analysis_domains(analysis)
    analysis.user_domain = user_domain
    analysis.competitor_domain = competitor_domain
    analysis.competitors = [competitor_domain]
    domains = [("own", "Ваш сайт", user_domain), ("competitor", "Конкурент", competitor_domain)]

    items = []
    analysis_errors = []
    for role, label, domain in domains:
        _check_canceled()
        audit = None
        audit_error = ""
        snapshot: dict[str, Any] = {"domain": domain, "error": ""}
        try:
            safe_domain = validate_public_analysis_domain(domain)
            _check_canceled()
            audit, audit_error = _run_existing_seo_audit(
                client=analysis.client,
                domain=safe_domain,
                stop_check=_stop_requested,
            )
            _check_canceled()
            try:
                snapshot = collect_domain_snapshot(safe_domain)
            except Exception as exc:
                logger.exception("competitor_analysis snapshot failed domain=%s", safe_domain)
                snapshot = {"domain": safe_domain, "error": str(exc)}
            _check_canceled()
            domain = safe_domain
        except DomainValidationError as exc:
            audit_error = str(exc)
            analysis_errors.append({"domain": domain, "error": audit_error})
        except Exception as exc:
            logger.exception("competitor_analysis domain failed domain=%s", domain)
            audit_error = str(exc) or "Не удалось выполнить анализ домена."
            analysis_errors.append({"domain": domain, "error": audit_error})

        result = _build_domain_result(
            role=role,
            label=label,
            domain=domain,
            audit=audit,
            audit_error=audit_error,
            snapshot=snapshot,
        )
        if result.get("error") and {"domain": domain, "error": result["error"]} not in analysis_errors:
            analysis_errors.append({"domain": domain, "error": result["error"]})
        items.append(result)

    recommendations = _build_recommendations(items)
    _check_canceled()
    payload = {
        "site_id": analysis.site_id,
        "site_name": analysis.site.name,
        "site_domain": user_domain,
        "user_domain": user_domain,
        "competitor_domain": competitor_domain,
        "generated_at": timezone.localtime(timezone.now()).isoformat(),
        "competitors": [competitor_domain],
        "items": items,
        "comparison": _build_comparison(items),
        "recommendations": recommendations,
        "improvement_plan": _build_improvement_plan(recommendations),
    }
    payload = _repair_report_payload_text(payload)

    pdf_bytes, filename = build_competitor_analysis_pdf(analysis=analysis, payload=payload)
    _check_canceled()
    if analysis.pdf_file:
        analysis.pdf_file.delete(save=False)
    analysis.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
    analysis.results = payload
    analysis.errors = analysis_errors
    analysis.status = CompetitorAnalysis.Status.COMPLETED
    analysis.finished_at = timezone.now()
    analysis.save(
        update_fields=[
            "user_domain",
            "competitor_domain",
            "competitors",
            "results",
            "errors",
            "pdf_file",
            "status",
            "finished_at",
            "updated_at",
        ]
    )
    return analysis
