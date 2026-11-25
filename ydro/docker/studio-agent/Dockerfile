FROM python:3.12-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=5
WORKDIR /opt/studio-agent
COPY requirements.txt .
# Keep verified downloads cached. If a proxy/CDN serves a broken response,
# retry without the HTTP cache; never bypass PyPI's SHA-256 checks.
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    set -eu; \
    if python -m pip install --index-url https://pypi.org/simple -r requirements.txt; then \
        python -m pip check; \
        exit 0; \
    fi; \
    echo "Initial dependency install failed; retrying with fresh downloads"; \
    for attempt in 1 2; do \
        sleep 5; \
        if python -m pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements.txt; then \
            python -m pip check; \
            exit 0; \
        fi; \
        echo "Fresh dependency download failed (attempt $attempt of 2)"; \
    done; \
    echo "Dependency installation failed. Integrity checks remain enabled."; \
    exit 1
COPY runner.py site_store.py test_site_store.py art_direction.py ./
RUN python -m unittest -v test_site_store && python runner.py --check
USER 10001:10001
ENTRYPOINT ["python", "/opt/studio-agent/runner.py"]
