import hashlib
import hmac
import json
import time
import uuid

import requests
from django.conf import settings


class AIServiceError(Exception):
    pass


class AIServiceTemporaryError(AIServiceError):
    pass


class AIServiceRejected(AIServiceError):
    pass


class AIRecommendationsClient:
    def __init__(self):
        self.base_url = settings.AI_RECOMMENDATIONS_SERVICE_URL.rstrip("/")
        self.timeout = settings.AI_RECOMMENDATIONS_TIMEOUT_SECONDS

    def _request(self, method, path, payload=None):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode() if payload is not None else b""
        timestamp, request_id = str(int(time.time())), str(uuid.uuid4())
        signature = hmac.new(
            settings.AI_RECOMMENDATIONS_SIGNING_SECRET.encode(),
            timestamp.encode() + request_id.encode() + body,
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "Authorization": f"Bearer {settings.AI_RECOMMENDATIONS_SERVICE_TOKEN}",
            "X-Timestamp": timestamp,
            "X-Request-Id": request_id,
            "X-Signature": signature,
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(method, self.base_url + path, data=body or None, headers=headers, timeout=self.timeout)
        except (requests.Timeout, requests.ConnectionError) as exc:
            raise AIServiceTemporaryError("AI-сервис временно недоступен.") from exc
        if response.status_code >= 500:
            raise AIServiceTemporaryError("AI-сервис временно недоступен.")
        if response.status_code >= 400:
            raise AIServiceRejected(f"AI-сервис отклонил запрос ({response.status_code}).")
        return response.json() if response.content else None

    def create_job(self, payload): return self._request("POST", "/api/v1/recommendations/jobs", payload)
    def get_job(self, job_id): return self._request("GET", f"/api/v1/recommendations/jobs/{job_id}")
    def by_external_id(self, external_id): return self._request("GET", f"/api/v1/recommendations/jobs/by-external-id/{external_id}")
    def retry_job(self, job_id): return self._request("POST", f"/api/v1/recommendations/jobs/{job_id}/retry")
    def delete_job(self, job_id): return self._request("DELETE", f"/api/v1/recommendations/jobs/{job_id}")

