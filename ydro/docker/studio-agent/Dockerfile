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
COPY runner.py site_store.py test_site_store.py art_direction.py media.py test_media.py landing-progress.js quality.py models3d.py test_models3d.py sketchfab_probe.py test_sketchfab_probe.py sketchfab_models.py test_sketchfab_models.py CinemaModel.vue asset_quality.py visual_critic.py test_visual_critic.py repair_input.py test_repair_input.py asset_preflight.py test_asset_preflight.py ./
RUN python -m unittest -v test_site_store test_media test_models3d test_sketchfab_probe test_sketchfab_models test_visual_critic test_repair_input test_asset_preflight && python runner.py --check
USER 10001:10001
ENTRYPOINT ["python", "/opt/studio-agent/runner.py"]
