"""Iteration 4 tests: regression after router split + new HMAC signed-URL flow."""
import io
import os
import time
import struct
import zlib
import pytest
import requests

def _load_base():
    v = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if v:
        return v.rstrip("/")
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    raise RuntimeError("REACT_APP_BACKEND_URL missing")


BASE = _load_base()
API = f"{BASE}/api"

ADMIN = {"email": "admin@assetflow.io", "password": "admin123"}
EMPLOYEE = {"email": "employee@assetflow.io", "password": "employee123"}


def _png_bytes():
    # Minimal 1x1 red PNG
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\x00\x00"
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def employee_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=EMPLOYEE, timeout=15)
    assert r.status_code == 200, r.text
    return s


# ---------------- Regression: auth ----------------
class TestAuthRegression:
    def test_login_admin(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN["email"]
        assert r.json()["role"] == "admin"

    def test_me_no_cookie_401(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_query_param_auth_rejected(self, admin_session):
        # Grab the access_token cookie and try to auth via ?auth=<jwt>
        token = admin_session.cookies.get("access_token")
        assert token, "access_token cookie missing"
        r = requests.get(f"{API}/auth/me", params={"auth": token})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


# ---------------- Regression: dashboard & assets ----------------
class TestDashboardAssets:
    def test_dashboard_stats(self, admin_session):
        r = admin_session.get(f"{API}/dashboard/stats")
        assert r.status_code == 200
        j = r.json()
        assert "total" in j or "total_assets" in j or isinstance(j, dict)

    def test_assets_list(self, admin_session):
        r = admin_session.get(f"{API}/assets")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------- Regression: audit ----------------
class TestAudit:
    def test_list_cycles(self, admin_session):
        r = admin_session.get(f"{API}/audit/cycles")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_and_close_cycle(self, admin_session):
        payload = {
            "name": f"TEST_it4_{int(time.time())}",
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "scope": "all",
        }
        r = admin_session.post(f"{API}/audit/cycles", json=payload)
        assert r.status_code in (200, 201), r.text
        cid = r.json().get("cycle_id") or r.json().get("id")
        assert cid
        # Close idempotently
        r2 = admin_session.post(f"{API}/audit/cycles/{cid}/close")
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert "missing_updated" in body and "damaged_updated" in body


# ---------------- Regression: departments (admin) ----------------
class TestDepartments:
    def test_create_dept_admin(self, admin_session):
        r = admin_session.post(f"{API}/departments", json={
            "name": f"TEST_dept_{int(time.time())}", "code": f"T{int(time.time())%10000}"
        })
        assert r.status_code in (200, 201), r.text

    def test_create_dept_employee_forbidden(self, employee_session):
        r = employee_session.post(f"{API}/departments", json={"name": "nope", "code": "X"})
        assert r.status_code == 403


# ---------------- Regression: brute-force lockout ----------------
class TestBruteForce:
    def test_lockout_after_5(self):
        email = f"TEST_bf_{int(time.time())}@ex.com"
        # user doesn't exist -> 401
        last = None
        for _ in range(6):
            last = requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
        assert last.status_code == 429, f"Expected 429 after 5 fails, got {last.status_code}"


# ---------------- NEW: HMAC signed URL flow ----------------
class TestSignedUrls:
    @pytest.fixture(scope="class")
    def uploaded(self, admin_session):
        png = _png_bytes()
        files = {"file": ("t.png", io.BytesIO(png), "image/png")}
        r = admin_session.post(f"{API}/uploads", files=files)
        assert r.status_code == 200, r.text
        j = r.json()
        assert "file_id" in j and "url" in j
        return {"file_id": j["file_id"], "png": png, "session": admin_session}

    def test_sign_returns_token(self, uploaded, admin_session):
        fid = uploaded["file_id"]
        r = admin_session.post(f"{API}/uploads/{fid}/sign")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["ttl_seconds"] == 300
        assert "expires_at" in j
        assert j["url"].startswith(f"/api/uploads/{fid}?token=")

    def test_signed_url_no_cookie_ok(self, uploaded, admin_session):
        fid = uploaded["file_id"]
        r = admin_session.post(f"{API}/uploads/{fid}/sign")
        signed_path = r.json()["url"]
        # Request without cookies
        r2 = requests.get(f"{BASE}{signed_path}")
        assert r2.status_code == 200, f"Expected 200 got {r2.status_code}"
        assert r2.content == uploaded["png"]

    def test_download_no_cookie_no_token_401(self, uploaded):
        fid = uploaded["file_id"]
        r = requests.get(f"{API}/uploads/{fid}")
        assert r.status_code == 401

    def test_invalid_token_401(self, uploaded):
        fid = uploaded["file_id"]
        r = requests.get(f"{API}/uploads/{fid}", params={"token": "garbage"})
        assert r.status_code == 401

    def test_tampered_token_401(self, uploaded, admin_session):
        fid = uploaded["file_id"]
        r = admin_session.post(f"{API}/uploads/{fid}/sign")
        signed_path = r.json()["url"]
        # tamper last char of token
        token = signed_path.split("token=")[1]
        tampered = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
        r2 = requests.get(f"{API}/uploads/{fid}", params={"token": tampered})
        assert r2.status_code == 401

    def test_query_auth_jwt_rejected_for_download(self, uploaded, admin_session):
        fid = uploaded["file_id"]
        jwt_token = admin_session.cookies.get("access_token")
        # old ?auth=<jwt> should no longer work
        r = requests.get(f"{API}/uploads/{fid}", params={"auth": jwt_token})
        assert r.status_code == 401
