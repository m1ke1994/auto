import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("CORE_SERVICE_TOKEN", "test-token")
os.environ.setdefault("AI_RECOMMENDATIONS_SIGNING_SECRET", "test-signing-secret")
os.environ.setdefault("AI_RECOMMENDATIONS_ENABLED", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.security import verify_request

engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)

@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def client():
    def db_override():
        with TestingSession() as session: yield session
    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[verify_request] = lambda: None
    with TestClient(app) as test_client: yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def payload():
    return {"external_job_id": "2fcf8834-c63e-497e-b3af-914fb692e938", "site_id": 8, "site_domain": "Example.COM", "recommendation_type": "combined", "language": "ru", "period": {"date_from": "2026-06-01", "date_to": "2026-06-30"}, "analytics": {"visits": 10}, "seo": {}, "options": {"max_recommendations": 10, "include_summary": True}}

