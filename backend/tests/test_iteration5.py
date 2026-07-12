"""Iteration 5 tests: covers allocations, bookings (409 overlap), maintenance move,
RBAC 403, health, and re-checks upload flow to guarantee iteration 5 code-quality
changes did not regress behaviour."""
import io
import os
import time
import struct
import zlib
import pytest
import requests


def _base():
    v = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if v:
        return v.rstrip("/")
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL missing")


BASE = _base()
API = f"{BASE}/api"
ADMIN = {"email": "admin@assetflow.io", "password": "admin123"}
EMPLOYEE = {"email": "employee@assetflow.io", "password": "employee123"}


def _png():
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


@pytest.fixture(scope="module")
def admin_s():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN, timeout=15)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def employee_s():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=EMPLOYEE, timeout=15)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def employee_me(employee_s):
    return employee_s.get(f"{API}/auth/me").json()


# ---------------- Health ----------------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{API}/health", timeout=10)
        assert r.status_code == 200

    def test_dashboard_stats_shape(self, admin_s):
        r = admin_s.get(f"{API}/dashboard/stats")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)


# ---------------- Upload flow (re-verify iter 5 defensive init did not break) ----------------
class TestUpload:
    def test_upload_and_sign(self, admin_s):
        files = {"file": ("t5.png", io.BytesIO(_png()), "image/png")}
        r = admin_s.post(f"{API}/uploads", files=files)
        assert r.status_code == 200, r.text
        fid = r.json()["file_id"]
        r2 = admin_s.post(f"{API}/uploads/{fid}/sign")
        assert r2.status_code == 200
        signed = r2.json()["url"]
        # Signed URL public GET (no cookies)
        r3 = requests.get(f"{BASE}{signed}")
        assert r3.status_code == 200

    def test_unauth_401(self):
        r = requests.get(f"{API}/uploads/does-not-exist")
        assert r.status_code == 401


# ---------------- Asset -> Allocation -> Return ----------------
@pytest.fixture(scope="module")
def a_category(admin_s):
    r = admin_s.get(f"{API}/categories")
    assert r.status_code == 200
    lst = r.json()
    if lst:
        return lst[0]["category_id"]
    r2 = admin_s.post(f"{API}/categories", json={"name": f"TEST_cat_{int(time.time())}"})
    assert r2.status_code in (200, 201), r2.text
    return r2.json().get("category_id") or r2.json().get("id")


@pytest.fixture(scope="module")
def a_asset(admin_s, a_category):
    payload = {
        "name": f"TEST_asset_{int(time.time())}",
        "category_id": a_category,
        "tag": f"TT{int(time.time())%100000}",
        "bookable": True,
        "condition": "good",
    }
    r = admin_s.post(f"{API}/assets", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["asset_id"]


class TestAllocation:
    def test_allocate_and_return(self, admin_s, a_asset, employee_me):
        # allocate
        r = admin_s.post(f"{API}/allocations", json={
            "asset_id": a_asset,
            "assignee_user_id": employee_me["user_id"],
            "notes": "TEST it5",
        })
        assert r.status_code in (200, 201), r.text
        alloc_id = r.json()["allocation_id"]
        # already allocated -> 409
        r2 = admin_s.post(f"{API}/allocations", json={
            "asset_id": a_asset, "assignee_user_id": employee_me["user_id"],
        })
        assert r2.status_code == 409
        # return
        r3 = admin_s.post(f"{API}/allocations/return", json={
            "allocation_id": alloc_id, "condition_notes": "ok"
        })
        assert r3.status_code == 200
        assert r3.json()["ok"] is True


# ---------------- Booking (409 overlap) ----------------
class TestBookingOverlap:
    def test_booking_overlap_409(self, admin_s, a_asset):
        start = "2027-05-01T10:00:00Z"
        end = "2027-05-01T12:00:00Z"
        r = admin_s.post(f"{API}/bookings", json={
            "asset_id": a_asset, "start_at": start, "end_at": end, "purpose": "TEST it5"
        })
        assert r.status_code in (200, 201), r.text
        # overlap
        r2 = admin_s.post(f"{API}/bookings", json={
            "asset_id": a_asset,
            "start_at": "2027-05-01T11:00:00Z",
            "end_at":   "2027-05-01T13:00:00Z",
            "purpose":  "overlap",
        })
        assert r2.status_code == 409, r2.text


# ---------------- Maintenance POST + move ----------------
class TestMaintenance:
    def test_create_and_move(self, admin_s, a_asset):
        r = admin_s.post(f"{API}/maintenance", json={
            "asset_id": a_asset, "issue": "TEST it5 issue", "priority": "medium",
        })
        assert r.status_code in (200, 201), r.text
        req_id = r.json()["request_id"]
        r2 = admin_s.post(f"{API}/maintenance/move", json={
            "request_id": req_id, "to_status": "approved", "technician": "tech1"
        })
        assert r2.status_code == 200


# ---------------- RBAC: 403 for employee on admin-only ----------------
class TestRBAC:
    def test_employee_cannot_create_dept(self, employee_s):
        r = employee_s.post(f"{API}/departments", json={"name": "nope", "code": "N1"})
        assert r.status_code == 403

    def test_employee_cannot_move_maintenance(self, employee_s, admin_s, a_asset):
        # admin creates a maint request first
        r = admin_s.post(f"{API}/maintenance", json={
            "asset_id": a_asset, "issue": "TEST rbac", "priority": "low",
        })
        req_id = r.json()["request_id"]
        r2 = employee_s.post(f"{API}/maintenance/move", json={
            "request_id": req_id, "to_status": "approved"
        })
        assert r2.status_code == 403
