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

