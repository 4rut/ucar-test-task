import os
import time
import pytest
import urllib.parse
import psycopg
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.api.deps import get_db
from app.main import app

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/incidents"
)


def _ensure_database_exists(db_url: str) -> None:
    if not db_url.startswith("postgresql+psycopg://"):
        return

    parsed = urllib.parse.urlparse(db_url)
    dbname = parsed.path.lstrip("/") or "postgres"
    server_url = db_url.replace(f"/{dbname}", "/postgres", 1)

    server_url_psycopg = server_url.replace("postgresql+psycopg://", "postgresql://", 1)
    target_db_psycog = db_url.replace("postgresql+psycopg://", "postgresql://", 1)

    try:
        with psycopg.connect(server_url_psycopg, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                exists = cur.fetchone() is not None
                if not exists:
                    cur.execute(f'CREATE DATABASE "{dbname}"')
    except Exception as e:
        print(f"[tests] WARNING: cannot ensure database exists: {e}")


@pytest.fixture(scope="session")
def engine():
    _ensure_database_exists(DB_URL)

    start = time.time()
    while time.time() - start < 10:
        try:
            eng = create_engine(DB_URL, future=True)
            with eng.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            break
        except Exception:
            time.sleep(0.5)
    else:
        eng = create_engine(DB_URL, future=True)
    return eng


@pytest.fixture(scope="session")
def testing_session_local(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def db_session(testing_session_local):
    session = testing_session_local()
    try:
        yield session
    finally:
        for tbl in reversed(Base.metadata.sorted_tables):
            session.execute(tbl.delete())
        session.commit()
        session.close()


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_create_incident_defaults_open(client):
    payload = {"description": "Scooter #42 offline", "source": "OPERATOR"}
    r = client.post("/incidents", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] >= 1
    assert body["description"] == payload["description"]
    assert body["status"] == "OPEN"
    assert body["source"] == "OPERATOR"
    assert "created_at" in body


def test_list_filter_by_status(client):
    client.post("/incidents", json={"description": "A", "source": "OPERATOR"})
    client.post("/incidents", json={"description": "B", "source": "MONITORING", "status": "RESOLVED"})
    r_all = client.get("/incidents")
    assert r_all.status_code == 200
    assert len(r_all.json()) == 2

    r_open = client.get("/incidents", params={"status": "OPEN"})
    assert r_open.status_code == 200
    items = r_open.json()
    assert len(items) == 1
    assert items[0]["description"] == "A"


def test_update_status_found(client):
    create = client.post("/incidents", json={"description": "C", "source": "PARTNER"}).json()
    incident_id = create["id"]
    r = client.patch(f"/incidents/{incident_id}/status", json={"status": "RESOLVED"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == incident_id
    assert body["status"] == "RESOLVED"


def test_update_status_not_found(client):
    r = client.patch("/incidents/9999/status", json={"status": "RESOLVED"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Incident not found"
