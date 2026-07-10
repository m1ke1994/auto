import pytest
from pydantic import ValidationError

from app.schemas import JobCreate, RecommendationResult


def test_domain_is_normalized(payload):
    assert JobCreate.model_validate(payload).site_domain == "example.com"

def test_invalid_period(payload):
    payload["period"] = {"date_from": "2026-07-01", "date_to": "2026-06-01"}
    with pytest.raises(ValidationError): JobCreate.model_validate(payload)

def test_result_is_strict():
    with pytest.raises(ValidationError):
        RecommendationResult.model_validate({"summary": "x", "score": 101, "recommendations": []})


def test_business_friendly_result_is_valid():
    result = RecommendationResult.model_validate(
        {
            "summary": "Мы нашли несколько способов сделать сайт полезнее для клиентов.",
            "score": 70,
            "recommendations": [
                {
                    "id": "rec-1",
                    "priority": "very_important",
                    "title": "Ускорьте загрузку сайта",
                    "why_important": "Если сайт долго открывается, часть посетителей уходит до знакомства с услугами.",
                    "actions": ["уменьшить размер изображений", "проверить скорость основных страниц"],
                    "benefit": "Больше посетителей смогут увидеть предложение компании и оставить заявку.",
                }
            ],
        }
    )
    assert result.recommendations[0].priority == "very_important"


def test_technical_language_is_rejected():
    with pytest.raises(ValidationError):
        RecommendationResult.model_validate(
            {
                "summary": "Проверьте robots.txt",
                "score": 50,
                "recommendations": [],
            }
        )
