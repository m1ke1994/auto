import re
import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

FORBIDDEN_PRESENTATION_TERMS = (
    "analytics.page_views",
    "analytics.events",
    "seo.pages",
    "seo.score",
    "canonical",
    "robots.txt",
    "json-ld",
    "structured data",
    "crawl",
    "crawler",
    " schema",
    "meta robots",
    "core web vitals",
    " lcp",
    " cls",
    " fid",
    " inp",
    "redirect",
    " 5xx",
    " 4xx",
    " h1",
    "meta description",
    " title",
    "sitemap",
    "search console",
    "google tag manager",
    "google analytics",
    "ga4",
    "яндекс метрика",
    "данных нет",
    "невозможно определить",
)


def validate_business_language(value: str) -> str:
    normalized = f" {value.casefold()}"
    term = next((item for item in FORBIDDEN_PRESENTATION_TERMS if item in normalized), None)
    if term:
        raise ValueError("user-facing text contains forbidden technical language")
    return value


class Period(BaseModel):
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def valid_range(self):
        if self.date_from > self.date_to:
            raise ValueError("date_from must not exceed date_to")
        if (self.date_to - self.date_from).days > 366:
            raise ValueError("period must not exceed 366 days")
        return self


class SiteContext(BaseModel):
    site_name: str = Field("", max_length=200)
    business_type: str = Field("", max_length=200)
    description: str = Field("", max_length=2000)


class JobOptions(BaseModel):
    max_recommendations: int = Field(10, ge=1, le=25)
    include_summary: bool = True


class JobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    external_job_id: uuid.UUID
    site_id: int = Field(gt=0)
    site_domain: str = Field(min_length=1, max_length=253)
    recommendation_type: Literal["seo", "conversion", "combined"]
    language: str = Field("ru", pattern=r"^[a-z]{2}$")
    period: Period
    site_context: SiteContext = Field(default_factory=SiteContext)
    analytics: dict[str, Any] = Field(default_factory=dict)
    seo: dict[str, Any] = Field(default_factory=dict)
    options: JobOptions = Field(default_factory=JobOptions)

    @field_validator("site_domain")
    @classmethod
    def normalize_domain(cls, value):
        value = value.strip().lower().rstrip(".")
        value = re.sub(r"^https?://", "", value).split("/", 1)[0]
        if not re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", value):
            raise ValueError("invalid domain")
        return value


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(max_length=100)
    priority: Literal["very_important", "recommended", "later"]
    title: str = Field(min_length=3, max_length=160)
    why_important: str = Field(min_length=10, max_length=1000)
    actions: list[str] = Field(min_length=1, max_length=5)
    benefit: str = Field(min_length=10, max_length=500)

    @field_validator("title", "why_important", "benefit")
    @classmethod
    def human_text(cls, value):
        return validate_business_language(value)

    @field_validator("actions")
    @classmethod
    def human_actions(cls, value):
        return [validate_business_language(item) for item in value]


class RecommendationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(max_length=2000)
    score: int = Field(ge=0, le=100)
    recommendations: list[Recommendation] = Field(max_length=25)

    @field_validator("summary")
    @classmethod
    def human_summary(cls, value):
        return validate_business_language(value)


class JobAccepted(BaseModel):
    job_id: uuid.UUID
    external_job_id: uuid.UUID
    status: str
    created_at: datetime


class JobResponse(JobAccepted):
    recommendation_type: str
    started_at: datetime | None
    completed_at: datetime | None
    result: RecommendationResult | None
    error: str | None
    openai_model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
