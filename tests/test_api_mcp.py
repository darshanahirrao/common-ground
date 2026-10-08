from fastapi.testclient import TestClient
from mcp import Client

from common_ground.api import create_app
from common_ground.mcp_server import mcp
from common_ground.qloo import QlooClient
from tests.test_planner import preview_request


def test_status_never_claims_live_validation_without_real_queries():
    client = TestClient(create_app(QlooClient("")))
    status = client.get("/api/status")
    assert status.json()["qloo_configured"] is False
    assert status.json()["live_validated"] is False
    assert status.headers["Cache-Control"] == "no-store"


def test_preview_end_to_end_and_evidence():
    client = TestClient(create_app(QlooClient("")))
    result = client.post("/api/plan", json=preview_request().model_dump())
    assert result.status_code == 200
    assert result.json()["candidates"][0]["name"] == "Night Ferry"
    assert result.json()["source"] == "synthetic"
    assert len(result.json()["query_steps"]) == 3
    assert client.get("/api/status").json()["live_validated"] is False


def test_live_mode_never_falls_back_to_preview():
    client = TestClient(create_app(QlooClient("")))
    result = client.get("/api/search?query=Fixture&source=qloo")
    assert result.status_code == 503
    assert "pending" in result.json()["detail"]
    assert "results" not in result.json()


def test_invalid_source_and_anchors_rejected():
    client = TestClient(create_app(QlooClient("")))
    assert client.get("/api/search?query=Fixture&source=invalid").status_code == 422
    request = preview_request().model_dump() | {"source": "qloo"}
    assert client.post("/api/plan", json=request).status_code == 422


def test_preview_anchor_search():
    client = TestClient(create_app(QlooClient("")))
    result = client.get("/api/search?query=Lantern&source=synthetic")
    assert result.json()["results"][0]["name"] == "The Lantern House"


def test_query_budget_protects_free_service():
    client = TestClient(create_app(QlooClient("")))
    for _ in range(30):
        assert client.get("/api/search?query=Lantern&source=synthetic").status_code == 200
    assert client.get("/api/search?query=Lantern&source=synthetic").status_code == 429


def test_oversized_requests_rejected():
    client = TestClient(create_app(QlooClient("")))
    assert client.post("/api/plan", content="x" * 17000).status_code == 413


def test_body_limit_does_not_trust_forged_content_length():
    client = TestClient(create_app(QlooClient("")))
    assert (
        client.post("/api/plan", content="x" * 17000, headers={"Content-Length": "0"}).status_code
        == 413
    )


def test_host_validation_and_security_headers():
    client = TestClient(create_app(QlooClient("")))
    assert client.get("/api/status", headers={"Host": "attacker.invalid"}).status_code == 400
    response = client.get("/api/status")
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "no-referrer"


async def test_mcp_tools_are_discoverable_with_official_sdk():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert names == {"search_cultural_anchors", "plan_movie_night"}


async def test_mcp_live_tool_without_key_returns_error_not_fiction(monkeypatch):
    monkeypatch.delenv("QLOO_API_KEY", raising=False)
    async with Client(mcp) as client:
        result = await client.call_tool("search_cultural_anchors", {"query": "Fixture"})
        assert result.is_error
