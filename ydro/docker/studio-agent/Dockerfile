FROM python:3.12-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=5
WORKDIR /opt/studio-agent
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements.txt && python -m pip check
COPY runner.py site_store.py test_site_store.py ./
RUN python -m unittest -v test_site_store && python runner.py --check
USER 10001:10001
ENTRYPOINT ["python", "/opt/studio-agent/runner.py"]
