"""Core API integration tests (signup → login → posts → like → comment → save)."""

from __future__ import annotations

import io
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def run_core_flow() -> dict:
    results: list[dict] = []
    suffix = uuid.uuid4().hex[:8]
    email = f"t{suffix}@example.com"
    username = f"test{suffix}"
    password = "testpass1"

    def step(name: str, fn):
        try:
            fn()
            results.append({"name": name, "ok": True, "detail": ""})
        except AssertionError as e:
            results.append({"name": name, "ok": False, "detail": str(e) or "assertion failed"})
        except Exception as e:
            results.append({"name": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})

    token_holder: dict[str, str] = {}
    post_id_holder: dict[str, int] = {}

    def signup():
        r = client.post(
            "/api/auth/signup",
            json={"email": email, "username": username, "full_name": "테스트", "password": password},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["access_token"]
        assert data["user"]["username"] == username
        token_holder["token"] = data["access_token"]

    def login():
        r = client.post("/api/auth/login", json={"username": username, "password": password})
        assert r.status_code == 200, r.text
        token_holder["token"] = r.json()["access_token"]

    def me():
        r = client.get("/api/auth/me", headers=auth(token_holder["token"]))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["username"] == username
        assert "posts_count" in body

    def create_post():
        r = client.post(
            "/api/posts",
            headers=auth(token_holder["token"]),
            data={"caption": "통합 테스트 #테스트", "location": "서울"},
            files=[("files", ("a.png", io.BytesIO(PNG), "image/png"))],
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["caption"] == "통합 테스트 #테스트"
        assert len(body["images"]) == 1
        post_id_holder["id"] = body["id"]

    def guest_feed():
        r = client.get("/api/posts/feed")
        assert r.status_code == 200
        assert "items" in r.json()

    def get_post():
        pid = post_id_holder["id"]
        r = client.get(f"/api/posts/{pid}")
        assert r.status_code == 200, r.text
        assert r.json()["id"] == pid

    def like_post():
        pid = post_id_holder["id"]
        r = client.post(f"/api/posts/{pid}/like", headers=auth(token_holder["token"]))
        assert r.status_code == 200, r.text
        r2 = client.get(f"/api/posts/{pid}", headers=auth(token_holder["token"]))
        assert r2.json()["liked"] is True
        assert r2.json()["likes_count"] >= 1

    def unlike_post():
        pid = post_id_holder["id"]
        r = client.delete(f"/api/posts/{pid}/like", headers=auth(token_holder["token"]))
        assert r.status_code == 200, r.text
        r2 = client.get(f"/api/posts/{pid}", headers=auth(token_holder["token"]))
        assert r2.json()["liked"] is False

    def comment():
        pid = post_id_holder["id"]
        r = client.post(
            f"/api/posts/{pid}/comments",
            headers=auth(token_holder["token"]),
            json={"body": "댓글 테스트"},
        )
        assert r.status_code == 201, r.text
        r2 = client.get(f"/api/posts/{pid}/comments")
        assert any(c["body"] == "댓글 테스트" for c in r2.json()["items"])

    def save_post():
        pid = post_id_holder["id"]
        r = client.post(f"/api/posts/{pid}/save", headers=auth(token_holder["token"]))
        assert r.status_code == 200, r.text
        r2 = client.get(f"/api/posts/{pid}", headers=auth(token_holder["token"]))
        assert r2.json()["saved"] is True

    def saved_tab():
        r = client.get(f"/api/users/{username}/saved", headers=auth(token_holder["token"]))
        assert r.status_code == 200, r.text
        ids = [x["id"] for x in r.json()["items"]]
        assert post_id_holder["id"] in ids

    def search():
        r = client.get("/api/search", params={"q": username})
        assert r.status_code == 200, r.text
        users = r.json()["users"]
        assert any(u["username"] == username for u in users)

    def duplicate_signup_409():
        r = client.post(
            "/api/auth/signup",
            json={"email": email, "username": username, "full_name": "x", "password": password},
        )
        assert r.status_code == 409, r.text

    def guest_like_401():
        pid = post_id_holder["id"]
        r = client.post(f"/api/posts/{pid}/like")
        assert r.status_code == 401, r.text

    step("POST /auth/signup", signup)
    step("POST /auth/login", login)
    step("GET /auth/me", me)
    step("POST /posts (multipart)", create_post)
    step("GET /posts/feed (guest)", guest_feed)
    step("GET /posts/{id}", get_post)
    step("POST /posts/{id}/like", like_post)
    step("DELETE /posts/{id}/like", unlike_post)
    step("POST /posts/{id}/comments", comment)
    step("POST /posts/{id}/save", save_post)
    step("GET /users/{username}/saved", saved_tab)
    step("GET /search", search)
    step("POST /auth/signup duplicate → 409", duplicate_signup_409)
    step("POST /posts/{id}/like without auth → 401", guest_like_401)

    return {"username": username, "post_id": post_id_holder.get("id"), "results": results}


if __name__ == "__main__":
    out = run_core_flow()
    passed = sum(1 for r in out["results"] if r["ok"])
    total = len(out["results"])
    for r in out["results"]:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"[{mark}] {r['name']}" + (f" — {r['detail']}" if r["detail"] else ""))
    print(f"\n{passed}/{total} passed (user={out['username']}, post={out.get('post_id')})")
    if passed != total:
        raise SystemExit(1)
