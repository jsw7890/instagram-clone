"""Demo account tests: follow, password, notifications, DM unread."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(username: str = "demo", password: str = "demo1234") -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def run_demo_tests() -> list[dict]:
    results: list[dict] = []

    def step(name: str, fn):
        try:
            fn()
            results.append({"name": name, "ok": True, "detail": ""})
        except AssertionError as e:
            results.append({"name": name, "ok": False, "detail": str(e) or "assertion failed"})
        except Exception as e:
            results.append({"name": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})

    token = login()
    h = auth(token)

    def follow_unfollow():
        r = client.post("/api/users/cara/follow", headers=h)
        assert r.status_code == 200, r.text
        prof = client.get("/api/users/cara", headers=h).json()
        assert prof["is_following"] is True
        r2 = client.delete("/api/users/cara/follow", headers=h)
        assert r2.status_code == 200, r2.text

    def password_change():
        r = client.post(
            "/api/auth/password",
            headers=h,
            json={"current_password": "demo1234", "new_password": "demo1234x"},
        )
        assert r.status_code == 200, r.text
        try:
            r2 = client.post(
                "/api/auth/login",
                json={"username": "demo", "password": "demo1234x"},
            )
            assert r2.status_code == 200, r.text
            r3 = client.post(
                "/api/auth/password",
                headers=auth(r2.json()["access_token"]),
                json={"current_password": "demo1234x", "new_password": "demo1234"},
            )
            assert r3.status_code == 200, r3.text
        finally:
            tail = client.post("/api/auth/login", json={"username": "demo", "password": "demo1234"})
            if tail.status_code != 200:
                tail = client.post("/api/auth/login", json={"username": "demo", "password": "demo1234x"})
                if tail.status_code == 200:
                    client.post(
                        "/api/auth/password",
                        headers=auth(tail.json()["access_token"]),
                        json={"current_password": "demo1234x", "new_password": "demo1234"},
                    )

    def notification_delete_one():
        lst = client.get("/api/notifications", headers=h).json()
        assert lst["items"], "no notifications to test delete"
        nid = lst["items"][0]["id"]
        before = len(lst["items"])
        r = client.delete(f"/api/notifications/{nid}", headers=h)
        assert r.status_code == 200, r.text
        lst2 = client.get("/api/notifications", headers=h).json()
        assert len(lst2["items"]) == before - 1

    def dm_unread():
        convs = client.get("/api/conversations", headers=h).json()
        alice = next((c for c in convs if c.get("other_user", {}).get("username") == "alice"), None)
        assert alice, "demo↔alice conversation missing"
        assert alice["unread_count"] >= 1, f"expected unread, got {alice['unread_count']}"

    def explore_authed():
        r = client.get("/api/posts/explore", headers=h)
        assert r.status_code == 200
        assert "items" in r.json()

    step("POST/DELETE /users/cara/follow", follow_unfollow)
    step("POST /auth/password + login rollback", password_change)
    step("DELETE /notifications/{id}", notification_delete_one)
    step("GET /conversations (alice unread)", dm_unread)
    step("GET /posts/explore (auth)", explore_authed)
    return results


if __name__ == "__main__":
    rows = run_demo_tests()
    for r in rows:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"[{mark}] {r['name']}" + (f" — {r['detail']}" if r["detail"] else ""))
    passed = sum(1 for r in rows if r["ok"])
    print(f"\n{passed}/{len(rows)} passed")
    if passed != len(rows):
        raise SystemExit(1)
