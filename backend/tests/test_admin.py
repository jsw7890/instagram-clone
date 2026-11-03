"""Admin API integration tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def admin_token() -> str:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "pass123"})
    assert r.status_code == 200, r.text
    me = client.get("/api/auth/me", headers=auth(r.json()["access_token"])).json()
    assert me.get("is_admin") is True
    return r.json()["access_token"]


def test_admin_forbidden_for_demo():
    r = client.post("/api/auth/login", json={"username": "demo", "password": "demo1234"})
    assert r.status_code == 200
    h = auth(r.json()["access_token"])
    assert client.get("/api/admin/stats", headers=h).status_code == 403


def test_admin_stats_and_lists():
    h = auth(admin_token())
    stats = client.get("/api/admin/stats", headers=h)
    assert stats.status_code == 200
    body = stats.json()
    assert "users" in body and "posts" in body
    users = client.get("/api/admin/users", headers=h, params={"limit": 5})
    assert users.status_code == 200
    assert "items" in users.json()
    posts = client.get("/api/admin/posts", headers=h, params={"limit": 5})
    assert posts.status_code == 200
    assert "items" in posts.json()
