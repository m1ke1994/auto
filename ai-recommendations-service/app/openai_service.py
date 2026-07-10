import json

from openai import OpenAI

from app.config import get_settings
from app.prompts.combined import PROMPT as COMBINED_PROMPT
from app.prompts.conversion import PROMPT as CONVERSION_PROMPT
from app.prompts.seo import PROMPT as SEO_PROMPT
from app.schemas import JobCreate, RecommendationResult

PROMPTS = {"seo": SEO_PROMPT, "conversion": CONVERSION_PROMPT, "combined": COMBINED_PROMPT}


def model_for(kind: str) -> str:
    settings = get_settings()
    return settings.OPENAI_MODEL_SEO if kind == "seo" else settings.OPENAI_MODEL_CONVERSION


def generate(payload: JobCreate):
    settings = get_settings()
    if not settings.AI_RECOMMENDATIONS_ENABLED:
        raise RuntimeError("AI recommendations are disabled")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key is not configured")
    model = model_for(payload.recommendation_type)
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_TIMEOUT_SECONDS)
    response = client.responses.parse(
        model=model,
        instructions=PROMPTS[payload.recommendation_type],
        input=json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
        text_format=RecommendationResult,
    )
    if response.output_parsed is None:
        raise ValueError("Model returned no valid structured result")
    usage = getattr(response, "usage", None)
    return response.output_parsed, model, getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)

