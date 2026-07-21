import pytest
import uuid
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_register_login_and_me():
    email = f"phase3-{uuid.uuid4().hex[:8]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "strongpass123", "full_name": "Phase Three"},
        )
        assert register.status_code == 201

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "strongpass123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == email


@pytest.mark.asyncio
async def test_guest_auth_and_admin_protection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        guest = await client.post("/api/v1/auth/guest")
        assert guest.status_code == 201
        token = guest.json()["access_token"]

        reindex = await client.post(
            "/api/v1/knowledge/reindex",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert reindex.status_code == 403


@pytest.mark.asyncio
async def test_smalltalk_does_not_trigger_retrieval_dump():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv = await client.post("/api/v1/chat/conversations", json={"title": "Smalltalk"})
        assert conv.status_code == 200
        conv_id = conv.json()["id"]

        resp = await client.post(
            f"/api/v1/chat/conversations/{conv_id}/messages",
            json={"content": "heyyy bot"},
        )
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "ready to explore" in content
        assert "Source Chunk" not in content
        assert "MCU Chronological Timeline" not in content


@pytest.mark.asyncio
async def test_character_question_returns_focused_answer():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conv = await client.post(
            "/api/v1/chat/conversations",
            json={"title": "Killmonger", "settings": {"spoiler_preference": "full"}},
        )
        assert conv.status_code == 200
        conv_id = conv.json()["id"]

        resp = await client.post(
            f"/api/v1/chat/conversations/{conv_id}/messages",
            json={"content": "Tell me about Killmonger", "settings": {"spoiler_preference": "full"}},
        )
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "Killmonger" in content
        assert "Source Chunk" not in content
        assert "retrieved from the database" not in content
        citations = resp.json()["citations"]
        assert citations
        assert any(citation.get("source_type") for citation in citations)
        assert any(citation.get("reason") for citation in citations)


@pytest.mark.asyncio
async def test_entity_graph_and_timeline_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        graph = await client.get("/api/v1/knowledge/entities/tony_stark/graph")
        assert graph.status_code == 200
        graph_data = graph.json()
        assert graph_data["center"]["id"] == "tony_stark"
        assert any(edge["target_entity_id"] == "peter_parker" for edge in graph_data["edges"])

        timeline = await client.get("/api/v1/knowledge/timeline?category=movies")
        assert timeline.status_code == 200
        timeline_data = timeline.json()
        assert timeline_data
        assert any(entry["title"] == "Avengers: Endgame" for entry in timeline_data)
