from unittest.mock import patch


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "tracknode-ai-recommendations"


@patch("app.main.process_job.delay")
def test_create_is_idempotent(delay, client, payload):
    first = client.post("/api/v1/recommendations/jobs", json=payload)
    second = client.post("/api/v1/recommendations/jobs", json=payload)
    assert first.status_code == 202
    assert first.json()["job_id"] == second.json()["job_id"]
    assert delay.call_count == 1


@patch("app.main.process_job.delay")
def test_get_delete_and_missing(delay, client, payload):
    job_id = client.post("/api/v1/recommendations/jobs", json=payload).json()["job_id"]
    assert client.get(f"/api/v1/recommendations/jobs/{job_id}").json()["status"] == "queued"
    assert client.delete(f"/api/v1/recommendations/jobs/{job_id}").status_code == 204
    assert client.get(f"/api/v1/recommendations/jobs/{job_id}").status_code == 404


def test_validation_rejects_bad_domain(client, payload):
    payload["site_domain"] = "https://bad domain.test"
    assert client.post("/api/v1/recommendations/jobs", json=payload).status_code == 422


def test_auth_is_required_without_override(client):
    from app.main import app
    from app.security import verify_request
    app.dependency_overrides.pop(verify_request)
    assert client.get("/api/v1/recommendations/jobs/00000000-0000-0000-0000-000000000000").status_code == 401

