from dataclasses import dataclass, field


_BOT_UA_PATTERNS = (
    ("googlebot", "googlebot"),
    ("bingbot", "bingbot"),
    ("yandexbot", "yandexbot"),
    ("duckduckbot", "duckduckbot"),
    ("baiduspider", "baiduspider"),
    ("slurp", "slurp"),
    ("facebookexternalhit", "facebookexternalhit"),
    ("telegrambot", "telegrambot"),
    ("whatsapp", "whatsapp"),
    ("applebot", "applebot"),
    ("twitterbot", "twitterbot"),
    ("linkedinbot", "linkedinbot"),
    ("slackbot", "slackbot"),
    ("discordbot", "discordbot"),
    ("vkshare", "vkshare"),
    ("crawler", "crawler"),
    ("spider", "spider"),
    ("robot", "robot"),
    ("bot", "bot"),
    ("preview", "preview"),
    ("headless", "headless"),
    ("lighthouse", "lighthouse"),
    ("chrome-lighthouse", "chrome-lighthouse"),
    ("pagespeed", "pagespeed"),
    ("gtmetrix", "gtmetrix"),
    ("pingdom", "pingdom"),
    ("uptime", "uptime"),
    ("monitor", "monitor"),
    ("ahrefsbot", "ahrefsbot"),
    ("semrushbot", "semrushbot"),
    ("mj12bot", "mj12bot"),
    ("dotbot", "dotbot"),
    ("petalbot", "petalbot"),
    ("bytespider", "bytespider"),
    ("scrapy", "scrapy"),
    ("curl", "curl"),
    ("wget", "wget"),
    ("python-requests", "python-requests"),
    ("httpclient", "httpclient"),
    ("http-client", "http-client"),
)


@dataclass
class BotCheckResult:
    is_bot: bool = False
    reasons: list[str] = field(default_factory=list)
    request_count_5s: int | None = None
    unique_urls_10s: int | None = None

    def add_reason(self, reason: str) -> None:
        if reason not in self.reasons:
            self.reasons.append(reason)
            self.is_bot = True

    @property
    def reason(self) -> str:
        return ", ".join(self.reasons)


def detect_bot_visit(
    *,
    site_id: int,
    ip_address: str | None,
    user_agent: str | None,
    tracked_url: str | None = None,
) -> BotCheckResult:
    # UA-only bot detection: it is deterministic and does not block regular visitors.
    _ = site_id, ip_address, tracked_url
    result = BotCheckResult()
    ua = (user_agent or "").strip()

    if not ua:
        result.add_reason("empty_user_agent")
        return result

    ua_lower = ua.lower()
    for token, name in _BOT_UA_PATTERNS:
        if token in ua_lower:
            result.add_reason(f"user_agent:{name}")

    return result
