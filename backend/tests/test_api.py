from fastapi.testclient import TestClient
from pymongo.errors import ConnectionFailure

from app.config import Settings
from app.main import create_app

TOKEN = "local-test-token-which-is-long-enough"


class MemoryRepository:
    """Test double only; the runnable application always uses MongoDB."""

    def __init__(self):
        self.records = {"schemes": {}, "cases": {}, "doorstep_requests": {}}

    async def seed(self, schemes):
        for scheme in schemes:
            self.records["schemes"][scheme.id] = scheme.model_dump(mode="json")

    async def list_schemes(self, query):
        return [
            s
            for s in self.records["schemes"].values()
            if query.casefold() in f"{s['title']} {s['category']}".casefold()
        ]

    async def get(self, collection, record_id):
        return self.records[collection].get(record_id)

    async def insert(self, collection, record):
        self.records[collection][record.id] = record.model_dump(mode="json")


def client(**overrides):
    config = dict(
        app_env="development",
        enable_demo_data=True,
        enable_dev_case_access=True,
        dev_access_token=TOKEN,
    )
    config.update(overrides)
    return TestClient(create_app(Settings(_env_file=None, **config), MemoryRepository()))


def test_discovery_and_case_round_trip():
    with client() as c:
        assert c.get("/api/health").json()["status"] == "ok"
        schemes = c.get("/api/schemes?q=education").json()
        assert len(schemes) == 1
        assert schemes[0]["is_demo"] is True
        scheme_id = schemes[0]["id"]
        assert c.get(f"/api/schemes/{scheme_id}").status_code == 200
        headers = {"X-Dev-Token": TOKEN}
        response = c.post(
            "/api/cases",
            headers=headers,
            json={"scheme_id": scheme_id, "assistance_type": "Guidance"},
        )
        assert response.status_code == 201
        record = response.json()
        assert c.get(f"/api/cases/{record['id']}", headers=headers).json() == record
        assert c.get(f"/api/cases/{record['id']}").status_code == 401
        assert c.get("/api/cases/missing", headers=headers).status_code == 404


def test_security_defaults_and_production_restriction():
    for config in (
        {"enable_dev_case_access": False},
        {"app_env": "production"},
        {"dev_access_token": "short"},
    ):
        with client(**config) as c:
            assert c.get("/api/cases/anything", headers={"X-Dev-Token": TOKEN}).status_code == 403
            assert c.post("/api/doorstep-requests", json={}).status_code == 403


def test_validation_and_doorstep():
    with client() as c:
        headers = {"X-Dev-Token": TOKEN}
        assert (
            c.post(
                "/api/cases",
                headers=headers,
                json={"scheme_id": "missing", "assistance_type": "Help"},
            ).status_code
            == 404
        )
        assert c.post("/api/cases", headers=headers, json={}).status_code == 422
        body = {
            "district": "Demo district",
            "service_type": "Guidance",
            "preferred_date": "2099-01-01",
        }
        assert c.post("/api/doorstep-requests", headers=headers, json=body).status_code == 201
        body["preferred_date"] = "2000-01-01"
        assert c.post("/api/doorstep-requests", headers=headers, json=body).status_code == 422
        body["phone"] = "should not be collected"
        assert c.post("/api/doorstep-requests", headers=headers, json=body).status_code == 422


def test_database_failure_returns_safe_error():
    class OfflineRepository(MemoryRepository):
        async def list_schemes(self, query):
            raise ConnectionFailure("internal connection information")

    with TestClient(create_app(Settings(_env_file=None), OfflineRepository())) as c:
        response = c.get("/api/health")
        assert response.status_code == 503
        assert "internal" not in response.text


def test_loopback_cors_and_untrusted_origin():
    with client() as c:
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            response = c.options(
                "/api/cases",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,x-dev-token",
                },
            )
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
        response = c.options(
            "/api/cases",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers


def test_non_ascii_configured_token_does_not_crash():
    with client(dev_access_token="\u00e9" * 32) as c:
        assert c.get("/api/cases/example", headers={"X-Dev-Token": TOKEN}).status_code == 401
