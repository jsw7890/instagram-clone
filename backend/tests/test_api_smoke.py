"""Smoke tests for all 41 API routes (backend.md §6.0)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(username: str = "demo", password: str = "demo1234") -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_guest_read_flow():
    assert client.get("/api/posts/feed").status_code == 200
    assert client.get("/api/posts/explore").status_code == 200
    suggested = client.get("/api/users/suggested").json()
    assert isinstance(suggested, list)
    assert client.get("/api/search", params={"q": "demo"}).status_code == 200
    assert client.get("/api/users/demo").status_code == 200
    posts = client.get("/api/users/demo/posts").json()["items"]
    if posts:
        pid = posts[0]["id"]
        assert client.get(f"/api/posts/{pid}").status_code == 200
        assert client.get(f"/api/posts/{pid}/comments").status_code == 200


def test_auth_and_profile():
    token = _login()
    h = auth(token)
    me = client.get("/api/auth/me", headers=h)
    assert me.status_code == 200
    assert me.json()["username"] == "demo"
    assert client.patch("/api/users/me", headers=h, json={"bio": "테스트"}).status_code == 200
    priv = client.get("/api/users/me/privacy", headers=h)
    assert priv.status_code == 200
    assert client.patch("/api/users/me/privacy", headers=h, json={"is_private": False}).status_code == 200
    assert client.get("/api/users/demo/followers").status_code == 200
    assert client.get("/api/users/demo/following").status_code == 200


def test_posts_stories_notifications_dm():
    token = _login()
    h = auth(token)
    feed = client.get("/api/posts/feed", headers=h).json()
    assert "items" in feed
    assert client.get("/api/stories/feed", headers=h).status_code == 200
    notifs = client.get("/api/notifications", headers=h).json()
    assert "has_unread" in notifs
    assert client.post("/api/notifications/read", headers=h).status_code == 200
    convs = client.get("/api/conversations", headers=h).json()
    assert isinstance(convs, list)
    if convs:
        cid = convs[0]["id"]
        assert client.get(f"/api/conversations/{cid}/messages", headers=h).status_code == 200
        assert client.post(f"/api/conversations/{cid}/read", headers=h).status_code == 200


def test_protected_requires_auth():
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/posts/1/like").status_code == 401


def test_suggested_excludes_following():
    token = _login("demo")
    h = auth(token)
    before = client.get("/api/users/suggested", headers=h).json()
    assert isinstance(before, list)
    names = {u["username"] for u in before}
    assert "alice" not in names and "bob" not in names
    assert names, "expected unfollowed users in suggestions"
    assert client.post("/api/users/cara/follow", headers=h).status_code == 200
    after = client.get("/api/users/suggested", headers=h).json()
    assert all(u["username"] != "cara" for u in after)
    client.delete("/api/users/cara/follow", headers=h)


def test_openapi_route_count():
    paths = set()
    for r in app.routes:
        if hasattr(r, "path") and r.path.startswith("/api"):
            for m in r.methods - {"HEAD", "OPTIONS"}:
                paths.add((m, r.path))
    assert len(paths) == 46
