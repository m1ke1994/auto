import json
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from .design import validate, demo_spec

class GenerationError(Exception):
    pass

SYSTEM = """You are a senior Russian-language web designer and information architect.
Return ONLY a JSON object (no markdown) with keys theme, brand, pages.
All text fields must be non-empty JSON strings, never objects or arrays.
The brand is the actual project name as a plain string, not a branding brief.
Example shape (replace every example text with project-specific content):
{"theme":"editorial","brand":"Atelier","pages":[{"label":"Главная","eyebrow":"Архитектура","heading":"Пространства для жизни","intro":"Описание проекта","items":[{"title":"Подход","text":"Описание подхода"},{"title":"Работы","text":"Описание работ"}]},{"label":"Контакты","eyebrow":"Связь","heading":"Обсудим проект","intro":"Уточните контакты","items":[{"title":"Почта","text":"Укажите email"},{"title":"Телефон","text":"Укажите номер"}]}]}
theme must be one of editorial, dark, modern, bold. brand is <=120 chars.
pages: 2-5 objects with label (<=40), eyebrow (<=80), heading (<=160),
intro (<=500), items (2-5 objects with title <=100 and text <=700).
Design meaningful navigation and specific, concise Russian copy for the user's domain.
Use varied editorial hierarchy, not generic filler. Never invent client names, testimonials,
prices, credentials or contacts. Mark unknown facts as placeholders. No HTML, JS, CSS, URLs,
or executable code. If previous design supplied, preserve all unrelated content and change only
what is requested. If a style requests 3D or cinematic, choose a matching visual direction,
but do not claim actual 3D functionality."""

def normalize_spec(raw, name, previous=None):
    """Repair representation of the brand only, never substitute demo pages."""
    if not isinstance(raw, dict):
        return raw
    raw = dict(raw)
    brand = raw.get("brand")
    if isinstance(brand, dict):
        brand = next((brand[k] for k in ("name", "title", "label", "brand_name")
                      if isinstance(brand.get(k), str) and brand[k].strip()), None)
    if not isinstance(brand, str) or not brand.strip() or len(brand.strip()) > 120:
        old_brand = previous.get("brand") if isinstance(previous, dict) else None
        brand = old_brand if isinstance(old_brand, str) and old_brand.strip() else name
    raw["brand"] = brand.strip()
    return raw

def mode():
    return getattr(settings,"STUDIO_AI_PROVIDER","demo")

def generate(name,prompt,style="auto",instruction="",previous=None):
    provider=mode()
    if provider=="demo":
        return demo_spec(name,prompt,style,instruction,previous)
    if provider not in ("yandex","deepseek"):
        raise GenerationError("Неизвестный AI-провайдер.")
    key=settings.STUDIO_AI_KEY
    model=settings.STUDIO_AI_MODEL
    folder=settings.STUDIO_AI_FOLDER
    if not key or not model or (provider=="yandex" and not folder):
        raise GenerationError("AI не настроен: проверьте ключ, модель и каталог.")
    if provider=="yandex":
        url="https://ai.api.cloud.yandex.net/v1/chat/completions"
        headers={"Authorization":"Api-Key "+key,"OpenAI-Project":folder}
        if not model.startswith("gpt://"):
            model=f"gpt://{folder}/{model}"
    else:
        url="https://api.deepseek.com/chat/completions"
        headers={"Authorization":"Bearer "+key}
    payload={"model":model,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":json.dumps({"name":name,"request":prompt,"style":style,"instruction":instruction,"previous":previous},ensure_ascii=False)}],"max_tokens":6000}
    if provider=="deepseek":
        # Structured output needs non-thinking mode on the current DeepSeek API.
        payload["thinking"]={"type":"disabled"}
        payload["response_format"]={"type":"json_object"}
    try:
        response=requests.post(url,headers=headers,json=payload,timeout=(8,75),allow_redirects=False)
        if not response.ok:
            raise GenerationError("AI API вернул HTTP "+str(response.status_code)+". Проверьте настройки и баланс.")
        if len(response.content)>200000:
            raise GenerationError("Ответ AI превышает допустимый размер.")
        choice=response.json()["choices"][0]
        if choice.get("finish_reason")=="length":
            raise GenerationError("AI не завершил ответ. Попробуйте сократить запрос.")
        content=choice["message"]["content"].strip()
        if content.startswith("\x60\x60\x60"):
            content=content.removeprefix("\x60\x60\x60json").removeprefix("\x60\x60\x60").removesuffix("\x60\x60\x60").strip()
        return validate(normalize_spec(json.loads(content),name,previous))
    except GenerationError:
        raise
    except ValidationError as exc:
        raise GenerationError("AI вернул данные вне схемы: " + "; ".join(exc.messages) + " Предыдущая версия сохранена.") from exc
    except (requests.RequestException,ValueError,KeyError,IndexError,TypeError,AttributeError) as exc:
        raise GenerationError("AI не вернул корректную дизайн-спецификацию. Предыдущая версия сохранена.") from exc
