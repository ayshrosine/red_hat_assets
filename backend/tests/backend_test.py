"""AssetFlow backend regression tests (pytest).

Covers: auth, RBAC, org setup, assets, allocation, transfer, booking,
maintenance, dashboard, activity, notifications.
Uses public REACT_APP_BACKEND_URL. Cookies are used across requests via
requests.Session.
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@assetflow.io", "password": "admin123"}
MANAGER = {"email": "manager@assetflow.io", "password": "manager123"}
HEAD = {"email": "head@assetflow.io", "password": "head123"}
EMP = {"email": "employee@assetflow.io", "password": "employee123"}


def _sess(creds=None):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    if creds:
        r = s.post(f"{API}/auth/login", json=creds)
        assert r.status_code == 200, f"login failed for {creds['email']}: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def admin_sess():
    return _sess(ADMIN)


@pytest.fixture(scope="session")
def emp_sess():
    return _sess(EMP)


@pytest.fixture(scope="session")
def head_sess():
    return _sess(HEAD)


# ---------- Health ----------
def test_health():
    r = requests.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ---------- Auth ----------
class TestAuth:
    def test_register_me_logout(self):
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        email = f"test_{uuid.uuid4().hex[:8]}@t.io"
        r = s.post(f"{API}/auth/register", json={"email": email, "password": "pw12345", "name": "T User"})
        assert r.status_code == 200, r.text
        u = r.json()
        assert u["email"] == email and u["role"] == "employee"
        # /me
        r2 = s.get(f"{API}/auth/me")
        assert r2.status_code == 200 and r2.json()["email"] == email
        # logout
        r3 = s.post(f"{API}/auth/logout")
        assert r3.status_code == 200
        # subsequent me
        r4 = s.get(f"{API}/auth/me")
        assert r4.status_code == 401

    def test_login_admin(self):
        s = _sess(ADMIN)
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 200 and r.json()["role"] == "admin"

    def test_login_wrong_password(self):
        # Use a unique email to isolate brute force counter
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": "admin@assetflow.io", "password": "WRONG_pw_xyz"})
        assert r.status_code == 401

    def test_forgot_password_no_leak(self):
        for em in ("admin@assetflow.io", f"nonexistent_{uuid.uuid4().hex[:6]}@x.io"):
            r = requests.post(f"{API}/auth/forgot-password", json={"email": em})
            assert r.status_code == 200 and r.json()["ok"] is True

    def test_brute_force_lockout(self):
        # Use a fresh throwaway account so we don't lock admin
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        email = f"bf_{uuid.uuid4().hex[:8]}@t.io"
        r = s.post(f"{API}/auth/register", json={"email": email, "password": "pw12345", "name": "BF"})
        assert r.status_code == 200
        s.post(f"{API}/auth/logout")
        # 5 wrong attempts -> next should 429
        codes = []
        for _ in range(6):
            rr = requests.post(f"{API}/auth/login", json={"email": email, "password": "nope-xxxxx"})
            codes.append(rr.status_code)
        assert 429 in codes, f"expected 429 lockout, got sequence {codes}"

    def test_google_session_invalid(self):
        r = requests.post(f"{API}/auth/google/session", json={"session_id": "invalid-xxx"})
        assert r.status_code == 401


# ---------- Org Setup ----------
class TestOrg:
    def test_department_crud_admin_only(self, admin_sess, emp_sess):
        # employee create -> 403
        r = emp_sess.post(f"{API}/departments", json={"name": "TEST_Dept"})
        assert r.status_code == 403
        # admin create
        r = admin_sess.post(f"{API}/departments", json={"name": f"TEST_Dept_{uuid.uuid4().hex[:6]}"})
        assert r.status_code == 200, r.text
        dep_id = r.json()["department_id"]
        # list
        r2 = admin_sess.get(f"{API}/departments")
        assert r2.status_code == 200 and any(d["department_id"] == dep_id for d in r2.json())
        # employee delete -> 403
        r3 = emp_sess.delete(f"{API}/departments/{dep_id}")
        assert r3.status_code == 403
        # admin delete
        r4 = admin_sess.delete(f"{API}/departments/{dep_id}")
        assert r4.status_code == 200

    def test_category_and_promote(self, admin_sess, emp_sess):
        r = admin_sess.post(f"{API}/categories", json={"name": f"TEST_Cat_{uuid.uuid4().hex[:6]}", "custom_fields": ["a", "b"]})
        assert r.status_code == 200, r.text
        cat_id = r.json()["category_id"]
        assert r.json()["custom_fields"] == ["a", "b"]
        # employee cannot create
        r2 = emp_sess.post(f"{API}/categories", json={"name": "nope"})
        assert r2.status_code == 403
        # delete
        assert admin_sess.delete(f"{API}/categories/{cat_id}").status_code == 200

        # promote — grab a throwaway user
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        em = f"promote_{uuid.uuid4().hex[:6]}@t.io"
        s.post(f"{API}/auth/register", json={"email": em, "password": "pw12345", "name": "P"})
        me = s.get(f"{API}/auth/me").json()
        # employee cannot promote
        rE = emp_sess.post(f"{API}/users/promote", json={"user_id": me["user_id"], "role": "asset_manager"})
        assert rE.status_code == 403
        # admin can
        rA = admin_sess.post(f"{API}/users/promote", json={"user_id": me["user_id"], "role": "asset_manager"})
        assert rA.status_code == 200


# ---------- Assets ----------
class TestAssets:
    def test_create_dup_and_filters(self, admin_sess, emp_sess):
        tag = f"TEST-{uuid.uuid4().hex[:8]}"
        payload = {"name": "TEST Laptop", "category_id": "cat_laptops", "tag": tag, "bookable": False}
        r = admin_sess.post(f"{API}/assets", json=payload)
        assert r.status_code == 200, r.text
        aid = r.json()["asset_id"]
        # duplicate tag
        r2 = admin_sess.post(f"{API}/assets", json=payload)
        assert r2.status_code == 400
        # employee cannot
        r3 = emp_sess.post(f"{API}/assets", json={**payload, "tag": tag + "-x"})
        assert r3.status_code == 403
        # filters
        r4 = admin_sess.get(f"{API}/assets", params={"q": tag})
        assert r4.status_code == 200 and any(a["asset_id"] == aid for a in r4.json())
        r5 = admin_sess.get(f"{API}/assets", params={"category_id": "cat_laptops"})
        assert r5.status_code == 200 and len(r5.json()) >= 1
        r6 = admin_sess.get(f"{API}/assets", params={"bookable": "true"})
        assert r6.status_code == 200 and all(a["bookable"] for a in r6.json())
        # get by id -> asset + allocations + maintenance
        r7 = admin_sess.get(f"{API}/assets/{aid}")
        assert r7.status_code == 200
        j = r7.json()
        assert "asset" in j and "allocations" in j and "maintenance" in j


# ---------- Allocation & Transfer ----------
class TestAllocationTransfer:
    @pytest.fixture(scope="class")
    def setup_asset_and_users(self, admin_sess):
        # create asset
        tag = f"ALLOC-{uuid.uuid4().hex[:8]}"
        r = admin_sess.post(f"{API}/assets", json={"name": "TEST Alloc Asset", "category_id": "cat_laptops", "tag": tag})
        assert r.status_code == 200
        aid = r.json()["asset_id"]
        users = admin_sess.get(f"{API}/users").json()
        emp = next(u for u in users if u["email"] == "employee@assetflow.io")
        head = next(u for u in users if u["email"] == "head@assetflow.io")
        return aid, emp["user_id"], head["user_id"]

    def test_double_alloc_and_return(self, admin_sess, setup_asset_and_users):
        aid, emp_id, _ = setup_asset_and_users
        r = admin_sess.post(f"{API}/allocations", json={"asset_id": aid, "assignee_user_id": emp_id})
        assert r.status_code == 200, r.text
        alloc_id = r.json()["allocation_id"]
        # asset now allocated
        a = admin_sess.get(f"{API}/assets/{aid}").json()["asset"]
        assert a["status"] == "allocated" and a["current_holder_id"] == emp_id
        # double allocate -> 409
        r2 = admin_sess.post(f"{API}/allocations", json={"asset_id": aid, "assignee_user_id": emp_id})
        assert r2.status_code == 409
        det = r2.json()["detail"]
        assert "current_holder" in det
        # return
        r3 = admin_sess.post(f"{API}/allocations/return", json={"allocation_id": alloc_id})
        assert r3.status_code == 200
        a2 = admin_sess.get(f"{API}/assets/{aid}").json()["asset"]
        assert a2["status"] == "available" and a2["current_holder_id"] is None

    def test_transfer_flow(self, admin_sess, emp_sess, setup_asset_and_users):
        aid, emp_id, head_id = setup_asset_and_users
        # allocate to employee first
        admin_sess.post(f"{API}/allocations", json={"asset_id": aid, "assignee_user_id": emp_id})
        # request transfer to head
        r = admin_sess.post(f"{API}/transfers", json={"asset_id": aid, "to_user_id": head_id, "reason": "swap"})
        assert r.status_code == 200
        tid = r.json()["transfer_id"]
        # employee cannot approve
        r2 = emp_sess.post(f"{API}/transfers/{tid}/approve")
        assert r2.status_code == 403
        # admin approve
        r3 = admin_sess.post(f"{API}/transfers/{tid}/approve")
        assert r3.status_code == 200
        a = admin_sess.get(f"{API}/assets/{aid}").json()["asset"]
        assert a["current_holder_id"] == head_id
        # reject flow on a new transfer
        r4 = admin_sess.post(f"{API}/transfers", json={"asset_id": aid, "to_user_id": emp_id, "reason": "back"})
        tid2 = r4.json()["transfer_id"]
        r5 = admin_sess.post(f"{API}/transfers/{tid2}/reject")
        assert r5.status_code == 200


# ---------- Booking ----------
class TestBooking:
    def test_booking_overlap_and_cancel(self, admin_sess):
        assets = admin_sess.get(f"{API}/assets", params={"bookable": "true"}).json()
        assert assets, "need a bookable asset"
        aid = assets[0]["asset_id"]
        from datetime import datetime, timezone, timedelta
        start = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(days=30, hours=2)).isoformat()
        r = admin_sess.post(f"{API}/bookings", json={"asset_id": aid, "start_at": start, "end_at": end, "purpose": "TEST"})
        assert r.status_code == 200, r.text
        bid = r.json()["booking_id"]
        # overlap
        overlap_end = (datetime.now(timezone.utc) + timedelta(days=30, hours=3)).isoformat()
        r2 = admin_sess.post(f"{API}/bookings", json={"asset_id": aid, "start_at": start, "end_at": overlap_end})
        assert r2.status_code == 409 and "conflict" in r2.json()["detail"]
        # cancel
        r3 = admin_sess.post(f"{API}/bookings/{bid}/cancel")
        assert r3.status_code == 200

    def test_booking_non_bookable(self, admin_sess):
        assets = admin_sess.get(f"{API}/assets", params={"bookable": "false"}).json()
        assert assets
        aid = assets[0]["asset_id"]
        from datetime import datetime, timezone, timedelta
        s = (datetime.now(timezone.utc) + timedelta(days=40)).isoformat()
        e = (datetime.now(timezone.utc) + timedelta(days=40, hours=1)).isoformat()
        r = admin_sess.post(f"{API}/bookings", json={"asset_id": aid, "start_at": s, "end_at": e})
        assert r.status_code == 400


# ---------- Maintenance ----------
class TestMaintenance:
    def test_maintenance_lifecycle(self, admin_sess):
        tag = f"MNT-{uuid.uuid4().hex[:8]}"
        r = admin_sess.post(f"{API}/assets", json={"name": "TEST Mnt Asset", "category_id": "cat_laptops", "tag": tag})
        aid = r.json()["asset_id"]
        m = admin_sess.post(f"{API}/maintenance", json={"asset_id": aid, "issue": "broken", "priority": "high"})
        assert m.status_code == 200
        rid = m.json()["request_id"]
        # approve
        admin_sess.post(f"{API}/maintenance/move", json={"request_id": rid, "to_status": "approved"})
        a = admin_sess.get(f"{API}/assets/{aid}").json()["asset"]
        assert a["status"] == "under_maintenance"
        # resolve
        admin_sess.post(f"{API}/maintenance/move", json={"request_id": rid, "to_status": "resolved"})
        a = admin_sess.get(f"{API}/assets/{aid}").json()["asset"]
        assert a["status"] == "available"


# ---------- Dashboard, Activity, Notifications ----------
class TestDashboard:
    def test_stats_keys(self, admin_sess):
        r = admin_sess.get(f"{API}/dashboard/stats")
        assert r.status_code == 200
        d = r.json()
        for k in ("total", "available", "allocated", "under_maintenance",
                  "active_bookings", "pending_transfers", "overdue", "upcoming_returns"):
            assert k in d and isinstance(d[k], int)

    def test_activity(self, admin_sess):
        r = admin_sess.get(f"{API}/activity")
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_notifications(self, admin_sess):
        r = admin_sess.get(f"{API}/notifications")
        assert r.status_code == 200
        r2 = admin_sess.post(f"{API}/notifications/read-all")
        assert r2.status_code == 200


# ---------- RBAC sweep ----------
class TestRBAC:
    def test_employee_forbidden_endpoints(self, emp_sess):
        cases = [
            ("POST", "/departments", {"name": "x"}),
            ("POST", "/assets", {"name": "x", "category_id": "cat_laptops", "tag": f"RB-{uuid.uuid4().hex[:6]}"}),
            ("POST", "/users/promote", {"user_id": "usr_x", "role": "employee"}),
        ]
        for method, path, body in cases:
            r = emp_sess.request(method, f"{API}{path}", json=body)
            assert r.status_code == 403, f"{path} expected 403 got {r.status_code}"
