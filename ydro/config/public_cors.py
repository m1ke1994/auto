import re

from corsheaders.conf import conf as cors_conf
from django.conf import settings
from django.http import HttpResponse
from django.utils.cache import patch_vary_headers


PUBLIC_CORS_PATH_PATTERNS = (
    re.compile(r"^/tracker\.js$"),
    re.compile(r"^/api/mini/tracker\.js$"),
    re.compile(r"^/api/sites/[^/]+/$"),
    re.compile(r"^/api/leads/$"),
    re.compile(r"^/leads/?$"),
    re.compile(r"^/api/public/"),
    re.compile(r"^/api/yadro-track/"),
    re.compile(r"^/api/(?:mini/)?track/(?:visit-start|pageview|event|visit-end)/$"),
    re.compile(r"^/api/(?:mini/)?analytics/event/$"),
    re.compile(r"^/api/mini/public/"),
)


def is_public_cors_path(path):
    return any(pattern.match(path) for pattern in PUBLIC_CORS_PATH_PATTERNS)


class PublicApiCorsMiddleware:
    """Allow credential-free browser access to public API routes only."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        enabled = settings.PUBLIC_API_CORS_ALLOW_ALL and is_public_cors_path(request.path_info)
        if (
            enabled
            and request.method == "OPTIONS"
            and request.headers.get("Access-Control-Request-Method")
        ):
            response = HttpResponse()
            response["Content-Length"] = "0"
        else:
            response = self.get_response(request)

        if not enabled or not request.headers.get("Origin"):
            return response

        patch_vary_headers(response, ("Origin",))
        response["Access-Control-Allow-Origin"] = "*"
        if "Access-Control-Allow-Credentials" in response:
            del response["Access-Control-Allow-Credentials"]

        if request.method == "OPTIONS":
            response["Access-Control-Allow-Methods"] = ", ".join(cors_conf.CORS_ALLOW_METHODS)
            response["Access-Control-Allow-Headers"] = ", ".join(cors_conf.CORS_ALLOW_HEADERS)
            if cors_conf.CORS_PREFLIGHT_MAX_AGE:
                response["Access-Control-Max-Age"] = str(cors_conf.CORS_PREFLIGHT_MAX_AGE)

        return response
