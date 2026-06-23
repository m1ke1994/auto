import re
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Article, HeroBlock, Review

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
# Typical mojibake artifacts when UTF-8 was decoded as cp1251/latin1.
MOJIBAKE_CHAR_RE = re.compile(r"[Ѓѓ‚„…†‡€‰Љ‹ЊЌЋЏђ‘’“”•–—™љ›њќћџ�°±µ]")
MOJIBAKE_TOKENS = (
    "РЎ",
    "Рђ",
    "Рџ",
    "Рќ",
    "С‚",
    "СЊ",
    "Сѓ",
    "СЏ",
    "Р°",
    "Рµ",
    "Рё",
    "Рѕ",
)


def looks_suspicious(text: str) -> bool:
    if not text:
        return False
    if MOJIBAKE_CHAR_RE.search(text):
        return True
    hits = sum(text.count(token) for token in MOJIBAKE_TOKENS)
    return hits >= 2


def readability_score(text: str) -> int:
    cyr = len(CYRILLIC_RE.findall(text))
    bad = len(MOJIBAKE_CHAR_RE.findall(text))
    question = text.count("?")
    return cyr - (bad * 4) - (question * 2)


def is_readable_russian(text: str) -> bool:
    return bool(CYRILLIC_RE.search(text)) and not MOJIBAKE_CHAR_RE.search(text)


def try_fix(text: str):
    original_score = readability_score(text)
    candidates = []

    methods = (
        ("cp1251->utf8", lambda value: value.encode("cp1251").decode("utf-8")),
        ("latin1->utf8", lambda value: value.encode("latin1").decode("utf-8")),
    )

    for method_name, transform in methods:
        try:
            candidate = transform(text)
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if candidate == text:
            continue
        candidates.append((method_name, candidate, readability_score(candidate)))

    if not candidates:
        return None, None

    method_name, best_candidate, best_score = max(candidates, key=lambda item: item[2])
    if best_score > original_score and is_readable_russian(best_candidate):
        return best_candidate, method_name
    return None, None


class Command(BaseCommand):
    help = "Fix mojibake text in content models where UTF-8 was saved via wrong decoding."

    model_fields = {
        Article: ("title", "preview_description", "content"),
        HeroBlock: ("title", "description"),
        Review: ("name", "event_name", "text"),
    }

    @transaction.atomic
    def handle(self, *args, **options):
        fixed_records = 0
        changed_fields_total = 0
        method_counter = Counter()

        self.stdout.write(self.style.WARNING("Scanning content models for mojibake..."))

        for model, fields in self.model_fields.items():
            for obj in model.objects.all().iterator():
                changed_fields = []
                methods_used = Counter()

                for field_name in fields:
                    value = getattr(obj, field_name, "")
                    if not isinstance(value, str) or not value:
                        continue
                    if not looks_suspicious(value):
                        continue

                    fixed_value, method_name = try_fix(value)
                    if fixed_value is None:
                        continue

                    setattr(obj, field_name, fixed_value)
                    changed_fields.append(field_name)
                    methods_used[method_name] += 1

                if changed_fields:
                    obj.save(update_fields=changed_fields)
                    fixed_records += 1
                    changed_fields_total += len(changed_fields)
                    method_counter.update(methods_used)
                    method_info = ", ".join(f"{k}: {v}" for k, v in methods_used.items())
                    self.stdout.write(
                        f"[FIXED] {model.__name__}(id={obj.pk}): {', '.join(changed_fields)} | {method_info}"
                    )

        self.stdout.write(self.style.SUCCESS("\nFix complete."))
        self.stdout.write(f"Records fixed: {fixed_records}")
        self.stdout.write(f"Fields changed: {changed_fields_total}")

        if method_counter:
            self.stdout.write("Methods used:")
            for method_name, count in method_counter.items():
                self.stdout.write(f"- {method_name}: {count}")
        else:
            self.stdout.write("Methods used: none (no mojibake detected)")
