"""Iteration 3 regression: audit date validation + idempotent close + uploads smoke."""
import io
import os
import uuid
import struct
import zlib
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@assetflow.io", "password": "admin123"}


def _sess(creds=None):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    if creds:
        r = s.post(f"{API}/auth/login", json=creds)
        assert r.status_code == 200, f"login: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def admin_sess():
    return _sess(ADMIN)


def _tiny_png() -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


class TestAuditDateValidation:
    def test_end_before_start_returns_400(self, admin_sess):
        r = admin_sess.post(f"{API}/audit/cycles", json={
            "name": f"TEST_bad_{uuid.uuid4().hex[:6]}",
            "start_date": "2026-02-15",
            "end_date": "2026-02-01",
        })
        assert r.status_code == 400, r.text
        assert "end_date" in r.text.lower() or "start" in r.text.lower()

    def test_end_equal_start_ok(self, admin_sess):
        r = admin_sess.post(f"{API}/audit/cycles", json={
            "name": f"TEST_same_{uuid.uuid4().hex[:6]}",
            "start_date": "2026-03-01",
            "end_date": "2026-03-01",
        })
        assert r.status_code == 200, r.text


class TestIdempotentClose:
    def test_close_twice_returns_shape(self, admin_sess):
        # Create cycle
        r = admin_sess.post(f"{API}/audit/cycles", json={
            "name": f"TEST_close_{uuid.uuid4().hex[:6]}",
            "start_date": "2026-04-01",
            "end_date": "2026-04-30",
        })
        assert r.status_code == 200, r.text
        cid = r.json()["cycle_id"]

        # First close
        r1 = admin_sess.post(f"{API}/audit/cycles/{cid}/close")
        assert r1.status_code == 200, r1.text
        b1 = r1.json()
        assert b1.get("ok") is True
        assert "missing_updated" in b1
        assert "damaged_updated" in b1

        # Second close (idempotent)
        r2 = admin_sess.post(f"{API}/audit/cycles/{cid}/close")
        assert r2.status_code == 200, r2.text
        b2 = r2.json()
        assert b2.get("ok") is True
        assert b2.get("message") is not None
        assert b2.get("missing_updated") == 0
        assert b2.get("damaged_updated") == 0


class TestUploadsSmoke:
    def test_upload_and_download(self, admin_sess):
        s = requests.Session()
        s.cookies.update(admin_sess.cookies)
        r = s.post(f"{API}/uploads", files={"file": ("smoke.png", _tiny_png(), "image/png")})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["content_type"] == "image/png"
        fid = data["file_id"]
        r2 = admin_sess.get(f"{API}/uploads/{fid}")
        assert r2.status_code == 200
        assert r2.headers.get("content-type", "").startswith("image/png")
