"""Iteration 2: Uploads, Audit Cycles, Overdue reminders, Google session guard.

Uses the same public REACT_APP_BACKEND_URL. Depends on seeded users:
admin@assetflow.io/admin123, manager, employee.
"""
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
MANAGER = {"email": "manager@assetflow.io", "password": "manager123"}
EMP = {"email": "employee@assetflow.io", "password": "employee123"}


def _sess(creds=None):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    if creds:
        r = s.post(f"{API}/auth/login", json=creds)
        assert r.status_code == 200, f"login {creds['email']}: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def admin_sess():
    return _sess(ADMIN)


@pytest.fixture(scope="module")
def manager_sess():
    return _sess(MANAGER)


@pytest.fixture(scope="module")
def emp_sess():
    return _sess(EMP)


def _tiny_png() -> bytes:
    """Return a minimal valid 1x1 PNG."""
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


# ------------------- UPLOADS -------------------
class TestUploads:
    def test_upload_requires_auth(self):
        r = requests.post(f"{API}/uploads", files={"file": ("a.png", _tiny_png(), "image/png")})
        assert r.status_code == 401

    def test_upload_and_download_png(self, admin_sess):
        png = _tiny_png()
        # multipart requires no JSON header
        s = requests.Session()
        s.cookies.update(admin_sess.cookies)
        r = s.post(f"{API}/uploads", files={"file": ("test.png", png, "image/png")})
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("file_id", "url", "content_type", "size", "filename"):
            assert k in data
        assert data["content_type"] == "image/png"
        assert data["filename"] == "test.png"
        assert data["size"] > 0
        # Download via cookie auth
        file_id = data["file_id"]
        r2 = admin_sess.get(f"{API}/uploads/{file_id}")
        assert r2.status_code == 200
        assert r2.headers.get("content-type", "").startswith("image/png")
        assert r2.content == png

    def test_upload_rejects_text(self, admin_sess):
        s = requests.Session()
        s.cookies.update(admin_sess.cookies)
        r = s.post(f"{API}/uploads", files={"file": ("a.txt", b"hello", "text/plain")})
        assert r.status_code == 400

    def test_download_via_query_auth(self, admin_sess):
        # Upload
        s = requests.Session()
        s.cookies.update(admin_sess.cookies)
        r = s.post(f"{API}/uploads", files={"file": ("q.png", _tiny_png(), "image/png")})
        assert r.status_code == 200
        file_id = r.json()["file_id"]
        # Grab access_token cookie
        token = admin_sess.cookies.get("access_token")
        assert token
        # Fresh session (no cookies) — use ?auth= query
        r2 = requests.get(f"{API}/uploads/{file_id}", params={"auth": token})
        assert r2.status_code == 200
        # Without auth
        r3 = requests.get(f"{API}/uploads/{file_id}")
        assert r3.status_code == 401


# ------------------- AUDIT CYCLES -------------------
class TestAudit:
    def test_employee_cannot_create_cycle(self, emp_sess):
        r = emp_sess.post(f"{API}/audit/cycles", json={
            "name": "should-fail",
            "start_date": "2026-01-01", "end_date": "2026-01-15",
        })
        assert r.status_code == 403

    def test_full_audit_workflow(self, admin_sess, manager_sess, emp_sess):
        # Get employee & manager user_ids
        users = admin_sess.get(f"{API}/users").json()
        emp = next(u for u in users if u["email"] == "employee@assetflow.io")
        # 1) admin creates cycle with employee assigned as auditor
        payload = {
            "name": f"TEST_Cycle_{uuid.uuid4().hex[:6]}",
            "start_date": "2026-01-01", "end_date": "2026-01-31",
            "auditor_ids": [emp["user_id"]],
        }
        r = admin_sess.post(f"{API}/audit/cycles", json=payload)
        assert r.status_code == 200, r.text
        cycle = r.json()
        cycle_id = cycle["cycle_id"]
        assert cycle["status"] == "in_progress"
        assert cycle["asset_count"] >= 1

        # 2) list has counts
        r2 = admin_sess.get(f"{API}/audit/cycles")
        assert r2.status_code == 200
        found = next(c for c in r2.json() if c["cycle_id"] == cycle_id)
        for k in ("verified", "missing", "damaged", "pending"):
            assert k in found["counts"]
        assert found["counts"]["pending"] == cycle["asset_count"]

        # 3) get detail
        r3 = admin_sess.get(f"{API}/audit/cycles/{cycle_id}")
        assert r3.status_code == 200
        det = r3.json()
        assert det["cycle"]["cycle_id"] == cycle_id
        items = det["items"]
        assert len(items) >= 3
        # Take 3 items to mark
        it_verify, it_missing, it_damaged = items[0], items[1], items[2]

        # 4) mark by employee-auditor (allowed since assigned)
        r4 = emp_sess.post(f"{API}/audit/items/{it_verify['item_id']}/mark", json={"result": "verified"})
        assert r4.status_code == 200, r4.text

        # 5) mark by admin
        assert admin_sess.post(f"{API}/audit/items/{it_missing['item_id']}/mark",
                               json={"result": "missing"}).status_code == 200
        assert admin_sess.post(f"{API}/audit/items/{it_damaged['item_id']}/mark",
                               json={"result": "damaged"}).status_code == 200

        # 6) Non-assigned employee gets 403 — create a second cycle w/o employee assigned
        payload2 = {
            "name": f"TEST_Cycle2_{uuid.uuid4().hex[:6]}",
            "start_date": "2026-01-01", "end_date": "2026-01-31",
            "auditor_ids": [],
        }
        c2 = admin_sess.post(f"{API}/audit/cycles", json=payload2).json()
        c2_items = admin_sess.get(f"{API}/audit/cycles/{c2['cycle_id']}").json()["items"]
        assert c2_items, "cycle2 should have items"
        r_deny = emp_sess.post(f"{API}/audit/items/{c2_items[0]['item_id']}/mark", json={"result": "verified"})
        assert r_deny.status_code == 403

        # 7) close cycle 1 (as manager)
        rc = manager_sess.post(f"{API}/audit/cycles/{cycle_id}/close")
        assert rc.status_code == 200, rc.text
        body = rc.json()
        assert body.get("ok") is True
        assert body.get("missing_updated", 0) >= 1
        assert body.get("damaged_updated", 0) >= 1

        # 8) further mark on closed cycle => 400
        r_late = admin_sess.post(f"{API}/audit/items/{it_verify['item_id']}/mark", json={"result": "verified"})
        assert r_late.status_code == 400
        assert "closed" in r_late.json().get("detail", "").lower()

        # 9) verify asset status was applied
        miss_asset = admin_sess.get(f"{API}/assets/{it_missing['asset_id']}").json()["asset"]
        assert miss_asset["status"] == "lost"
        dam_asset = admin_sess.get(f"{API}/assets/{it_damaged['asset_id']}").json()["asset"]
        assert dam_asset["status"] == "under_maintenance"


# ------------------- OVERDUE -------------------
class TestOverdue:
    def test_employee_cannot_trigger(self, emp_sess):
        r = emp_sess.post(f"{API}/overdue/check")
        assert r.status_code == 403

    def test_admin_trigger_and_dedupe(self, admin_sess):
        # Seed an overdue allocation: create an asset, allocate to employee with past expected_return
        tag = f"OVD-{uuid.uuid4().hex[:6]}"
        a = admin_sess.post(f"{API}/assets", json={"name": "TEST Overdue", "category_id": "cat_laptops", "tag": tag}).json()
        users = admin_sess.get(f"{API}/users").json()
        emp = next(u for u in users if u["email"] == "employee@assetflow.io")
        # past date
        from datetime import datetime, timezone, timedelta
        past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        alloc = admin_sess.post(f"{API}/allocations", json={
            "asset_id": a["asset_id"], "assignee_user_id": emp["user_id"],
            "expected_return": past,
        }).json()
        assert "allocation_id" in alloc, alloc

        # First trigger
        r1 = admin_sess.post(f"{API}/overdue/check")
        assert r1.status_code == 200 and r1.json().get("ok") is True

        # employee's notifications should have overdue kind
        e_sess = _sess(EMP)
        notifs = e_sess.get(f"{API}/notifications").json()
        overdue = [n for n in notifs if n["kind"] == "overdue_return" and a["asset_id"] in str(n.get("meta", {}))]
        # Might match by allocation_id in meta
        overdue = [n for n in notifs if n["kind"] == "overdue_return"]
        count_before = len(overdue)
        assert count_before >= 1

        # Second trigger — should dedupe (same day)
        r2 = admin_sess.post(f"{API}/overdue/check")
        assert r2.status_code == 200
        notifs2 = e_sess.get(f"{API}/notifications").json()
        count_after = len([n for n in notifs2 if n["kind"] == "overdue_return"])
        assert count_after == count_before, f"dedupe failed: before={count_before} after={count_after}"


# ------------------- GOOGLE OAUTH GUARD -------------------
class TestGoogleGuard:
    def test_fake_session_id(self):
        r = requests.post(f"{API}/auth/google/session", json={"session_id": "invalid-xxx"})
        assert r.status_code == 401
        assert "Invalid session" in r.text or "invalid" in r.text.lower()
