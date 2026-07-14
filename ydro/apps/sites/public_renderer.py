import re
from html import escape

from django.conf import settings

from clients.services import get_user_client
from subscriptions.access import billing_is_enabled, has_active_subscription


def public_billing_url() -> str:
    base_url = str(getattr(settings, "SITE_BASE_URL", "https://tracknode.ru") or "https://tracknode.ru").rstrip("/")
    return f"{base_url}/login?redirect=/billing"


def site_requires_subscription_lock(site) -> bool:
    if not billing_is_enabled():
        return False
    client = get_user_client(getattr(site, "owner", None))
    return not (client and client.is_active and has_active_subscription(client))


def inject_subscription_lock(index_html: str, billing_url: str) -> str:
    safe_billing_url = escape(str(billing_url), quote=True)
    markup = f"""
<style id="tracknode-subscription-lock-style">
  html, body {{ overflow: hidden !important; }}
  #tracknode-subscription-lock {{
    position: fixed; inset: 0; z-index: 2147483647; display: flex;
    align-items: center; justify-content: center; box-sizing: border-box;
    width: 100vw; min-height: 100vh; min-height: 100dvh; padding: 20px;
    background: rgba(15, 23, 42, .76); backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px); overflow: auto; overscroll-behavior: contain;
  }}
  #tracknode-subscription-lock .tracknode-lock-card {{
    box-sizing: border-box; width: min(100%, 520px); padding: 32px;
    border-radius: 24px; background: #fff; color: #0f172a; text-align: center;
    box-shadow: 0 24px 80px rgba(0, 0, 0, .28); font-family: Arial, sans-serif;
  }}
  #tracknode-subscription-lock .tracknode-lock-icon {{
    display: flex; align-items: center; justify-content: center; width: 64px;
    height: 64px; margin: 0 auto 20px; border-radius: 50%; background: #fff7ed;
    color: #ea580c; font-size: 32px; font-weight: 700;
  }}
  #tracknode-subscription-lock h1 {{ margin: 0 0 16px; font-size: clamp(24px, 4vw, 32px); line-height: 1.2; }}
  #tracknode-subscription-lock p {{ margin: 0 0 24px; color: #475569; font-size: 16px; line-height: 1.6; }}
  #tracknode-subscription-lock a {{
    display: inline-flex; align-items: center; justify-content: center; min-height: 48px;
    padding: 0 24px; border-radius: 14px; background: #2563eb; color: #fff;
    text-decoration: none; font-weight: 700;
  }}
  #tracknode-subscription-lock small {{ display: block; margin-top: 18px; color: #94a3b8; }}
  @media (max-width: 480px) {{
    #tracknode-subscription-lock {{ padding: 14px; }}
    #tracknode-subscription-lock .tracknode-lock-card {{ padding: 24px 20px; }}
  }}
</style>
<div id="tracknode-subscription-lock" role="dialog" aria-modal="true" aria-labelledby="tracknode-subscription-lock-title">
  <div class="tracknode-lock-card">
    <div class="tracknode-lock-icon" aria-hidden="true">!</div>
    <h1 id="tracknode-subscription-lock-title">Работа сайта временно приостановлена</h1>
    <p>Доступ к сайту ограничен, поскольку срок действия тарифа истёк или он не был оплачен.<br><br>Для восстановления полноценной работы сайта владельцу необходимо войти в личный кабинет TrackNode и продлить подписку.</p>
    <a href="{safe_billing_url}">Перейти в личный кабинет</a>
    <small>Сайт работает на платформе TrackNode</small>
  </div>
</div>
<script id="tracknode-subscription-lock-script">
  (function () {{
    document.documentElement.style.setProperty('overflow', 'hidden', 'important');
    if (document.body) document.body.style.setProperty('overflow', 'hidden', 'important');
    document.addEventListener('keydown', function (event) {{
      if (event.key === 'Escape') {{ event.preventDefault(); event.stopImmediatePropagation(); }}
    }}, true);
  }})();
</script>
"""
    if re.search(r"</body\s*>", index_html, flags=re.IGNORECASE):
        return re.sub(r"</body\s*>", f"{markup}</body>", index_html, count=1, flags=re.IGNORECASE)
    return f"{index_html}{markup}"
