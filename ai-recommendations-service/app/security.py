import hashlib
import hmac
import ipaddress
import time

from fastapi import HTTPException, Request
from redis import Redis

from app.config import get_settings


async def verify_request(request: Request):
    settings = get_settings()
    authorization = request.headers.get("authorization", "")
    token = authorization[7:] if authorization.startswith("Bearer ") else ""
    if not token or not settings.CORE_SERVICE_TOKEN or not hmac.compare_digest(token, settings.CORE_SERVICE_TOKEN):
        raise HTTPException(401, "Invalid service credentials")
    client_ip = request.client.host if request.client else ""
    if settings.allowed_ips and not any(ipaddress.ip_address(client_ip) in ipaddress.ip_network(net, strict=False) for net in settings.allowed_ips):
        raise HTTPException(403, "Source IP is not allowed")
    timestamp, request_id, signature = (request.headers.get(name, "") for name in ("x-timestamp", "x-request-id", "x-signature"))
    try:
        if abs(time.time() - int(timestamp)) > 300:
            raise ValueError
    except ValueError:
        raise HTTPException(401, "Invalid or expired timestamp") from None
    if not request_id or not signature:
        raise HTTPException(401, "Missing request signature")
    body = await request.body()
    expected = hmac.new(settings.AI_RECOMMENDATIONS_SIGNING_SECRET.encode(), timestamp.encode() + request_id.encode() + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Invalid request signature")
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        if not redis.set(f"request:{request_id}", "1", ex=600, nx=True):
            raise HTTPException(409, "Request ID has already been used")
        bucket = f"rate:{client_ip}:{int(time.time()) // settings.RATE_LIMIT_WINDOW_SECONDS}"
        count = redis.incr(bucket)
        if count == 1:
            redis.expire(bucket, settings.RATE_LIMIT_WINDOW_SECONDS + 1)
        if count > settings.RATE_LIMIT_REQUESTS:
            raise HTTPException(429, "Rate limit exceeded")
    finally:
        redis.close()
