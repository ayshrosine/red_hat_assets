"""AssetFlow — Enterprise Asset & Resource Management API."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import logging
import secrets
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal

import bcrypt
import jwt
import httpx
from bson import ObjectId
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, Query, UploadFile, File, status
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import Response as FastAPIResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from storage import init_storage, put_object, get_object, build_path
from emailer import send_email, overdue_email_html
from scheduler import overdue_reminder_loop, run_overdue_check_now

# ---------- Config ----------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_MIN = 60 * 24  # 24h for demo comfort
REFRESH_DAYS = 7

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("assetflow")

app = FastAPI(title="AssetFlow API")
api = APIRouter(prefix="/api")

# ---------- Constants ----------
ROLES = ["admin", "asset_manager", "department_head", "employee"]
ASSET_STATUSES = ["available", "allocated", "reserved", "under_maintenance", "lost", "retired", "disposed"]
MAINT_STATUSES = ["pending", "approved", "assigned", "in_progress", "resolved", "rejected"]
TRANSFER_STATUSES = ["requested", "approved", "rejected", "completed"]
BOOKING_STATUSES = ["upcoming", "ongoing", "completed", "cancelled"]

# ---------- Helpers ----------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id, "email": email, "type": "access",
        "exp": now_utc() + timedelta(minutes=ACCESS_MIN),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "type": "refresh", "exp": now_utc() + timedelta(days=REFRESH_DAYS)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_auth_cookies(response: Response, access: str, refresh: str):
    response.set_cookie("access_token", access, httponly=True, secure=True, samesite="none", max_age=ACCESS_MIN * 60, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="none", max_age=REFRESH_DAYS * 86400, path="/")


def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    response.delete_cookie("session_token", path="/")


def clean_user(u: dict) -> dict:
    if not u:
        return u
    u = dict(u)
    u.pop("_id", None)
    u.pop("password_hash", None)
    for k in ("created_at", "updated_at"):
        if isinstance(u.get(k), datetime):
            u[k] = iso(u[k])
    return u


async def get_current_user(request: Request) -> dict:
    # Try JWT cookie
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") == "access":
                user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
                if user:
                    user.pop("password_hash", None)
                    return user
        except jwt.PyJWTError:
            pass
    # Try Emergent session_token cookie
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            session_token = auth[7:]
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > now_utc():
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    user.pop("password_hash", None)
                    return user
    raise HTTPException(status_code=401, detail="Not authenticated")


def require_roles(*roles: str):
    async def _dep(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(roles)}")
        return user
    return _dep


async def log_activity(actor: dict, action: str, kind: str, target_id: str = "", target_name: str = "", meta: Optional[dict] = None):
    doc = {
        "activity_id": new_id("act"),
        "actor_id": actor.get("user_id"),
        "actor_name": actor.get("name"),
        "action": action,
        "kind": kind,
        "target_id": target_id,
        "target_name": target_name,
        "meta": meta or {},
        "created_at": iso(now_utc()),
    }
    await db.activity_logs.insert_one(doc)


async def add_notification(user_id: str, kind: str, title: str, body: str = "", meta: Optional[dict] = None):
    doc = {
        "notif_id": new_id("ntf"),
        "user_id": user_id,
        "kind": kind,
        "title": title,
        "body": body,
        "meta": meta or {},
        "read": False,
        "created_at": iso(now_utc()),
    }
    await db.notifications.insert_one(doc)


# ---------- Models ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class GoogleSessionIn(BaseModel):
    session_id: str


class PromoteIn(BaseModel):
    user_id: str
    role: Literal["admin", "asset_manager", "department_head", "employee"]
    department_id: Optional[str] = None


class DepartmentIn(BaseModel):
    name: str
    head_user_id: Optional[str] = None
    parent_id: Optional[str] = None
    active: bool = True


class CategoryIn(BaseModel):
    name: str
    icon: Optional[str] = "package"
    custom_fields: List[str] = []


class AssetIn(BaseModel):
    name: str
    category_id: str
    tag: str
    serial: Optional[str] = ""
    department_id: Optional[str] = None
    location: str = ""
    condition: Literal["new", "good", "fair", "poor"] = "good"
    acquisition_date: Optional[str] = None
    acquisition_cost: Optional[float] = 0
    bookable: bool = False
    photo_url: Optional[str] = ""
    photo_urls: List[str] = []
    doc_urls: List[str] = []
    notes: Optional[str] = ""
    custom_data: dict = {}


class AllocateIn(BaseModel):
    asset_id: str
    assignee_user_id: str
    expected_return: Optional[str] = None
    notes: Optional[str] = ""


class TransferRequestIn(BaseModel):
    asset_id: str
    to_user_id: str
    reason: str = ""


class ReturnIn(BaseModel):
    allocation_id: str
    condition_notes: str = ""


class BookingIn(BaseModel):
    asset_id: str
    start_at: str  # ISO string
    end_at: str
    purpose: str = ""


class MaintenanceIn(BaseModel):
    asset_id: str
    issue: str
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    photo_url: Optional[str] = ""


class MaintenanceMoveIn(BaseModel):
    request_id: str
    to_status: Literal["pending", "approved", "assigned", "in_progress", "resolved", "rejected"]
    technician: Optional[str] = ""
    resolution_notes: Optional[str] = ""


# ============================================================
# AUTH ROUTES
# ============================================================
@api.post("/auth/register")
async def register(payload: RegisterIn, response: Response):
    email = payload.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = new_id("usr")
    doc = {
        "user_id": user_id,
        "email": email,
        "name": payload.name.strip(),
        "password_hash": hash_password(payload.password),
        "role": "employee",
        "department_id": None,
        "avatar": "",
        "auth_provider": "password",
        "created_at": iso(now_utc()),
    }
    await db.users.insert_one(doc)
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    return clean_user(doc)


@api.post("/auth/login")
async def login(payload: LoginIn, response: Response, request: Request):
    email = payload.email.lower().strip()
    ident = email  # key on email only — k8s ingress makes per-IP tracking unreliable
    # brute force check
    attempt = await db.login_attempts.find_one({"identifier": ident})
    if attempt and attempt.get("count", 0) >= 5:
        locked_until = attempt.get("locked_until")
        if locked_until:
            lu = datetime.fromisoformat(locked_until) if isinstance(locked_until, str) else locked_until
            if lu.tzinfo is None:
                lu = lu.replace(tzinfo=timezone.utc)
            if lu > now_utc():
                raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        new_count = (attempt.get("count", 0) if attempt else 0) + 1
        update = {"$set": {"count": new_count}}
        # only stamp locked_until when we cross the threshold, not on every failure
        if new_count >= 5:
            update["$set"]["locked_until"] = iso(now_utc() + timedelta(minutes=15))
        await db.login_attempts.update_one({"identifier": ident}, update, upsert=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await db.login_attempts.delete_one({"identifier": ident})
    access = create_access_token(user["user_id"], email)
    refresh = create_refresh_token(user["user_id"])
    set_auth_cookies(response, access, refresh)
    return clean_user(user)


@api.post("/auth/logout")
async def logout(response: Response, request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    clear_auth_cookies(response)
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return clean_user(user)


@api.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    tok = request.cookies.get("refresh_token")
    if not tok:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(user["user_id"], user["email"])
    response.set_cookie("access_token", access, httponly=True, secure=True, samesite="none", max_age=ACCESS_MIN * 60, path="/")
    return {"ok": True}


@api.post("/auth/forgot-password")
async def forgot_password(payload: ForgotIn):
    user = await db.users.find_one({"email": payload.email.lower().strip()})
    # Always return ok (do not leak account existence)
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token": token,
            "user_id": user["user_id"],
            "used": False,
            "expires_at": now_utc() + timedelta(hours=1),
            "created_at": iso(now_utc()),
        })
        log.info(f"[PWD-RESET] Reset link for {user['email']}: /reset-password?token={token}")
    return {"ok": True, "message": "If that email exists, a reset link has been sent."}


@api.post("/auth/reset-password")
async def reset_password(payload: ResetIn):
    rec = await db.password_reset_tokens.find_one({"token": payload.token, "used": False})
    if not rec:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    exp = rec["expires_at"]
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now_utc():
        raise HTTPException(status_code=400, detail="Token expired")
    await db.users.update_one({"user_id": rec["user_id"]}, {"$set": {"password_hash": hash_password(payload.new_password)}})
    await db.password_reset_tokens.update_one({"token": payload.token}, {"$set": {"used": True}})
    return {"ok": True}


@api.post("/auth/google/session")
async def google_session(payload: GoogleSessionIn, response: Response):
    """Exchange Emergent session_id for a session_token; create or update user."""
    async with httpx.AsyncClient(timeout=15) as httpc:
        r = await httpc.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": payload.session_id},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    data = r.json()
    email = data["email"].lower().strip()
    session_token = data["session_token"]
    existing = await db.users.find_one({"email": email})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one({"user_id": user_id}, {"$set": {
            "name": data.get("name") or existing.get("name"),
            "avatar": data.get("picture") or existing.get("avatar", ""),
        }})
    else:
        user_id = new_id("usr")
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": data.get("name", email.split("@")[0]),
            "avatar": data.get("picture", ""),
            "role": "employee",
            "department_id": None,
            "auth_provider": "google",
            "created_at": iso(now_utc()),
        })
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": now_utc() + timedelta(days=7),
        "created_at": iso(now_utc()),
    })
    response.set_cookie("session_token", session_token, httponly=True, secure=True, samesite="none", max_age=7 * 86400, path="/")
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return clean_user(user)


# ============================================================
# USERS & ORG SETUP
# ============================================================
@api.get("/users")
async def list_users(user: dict = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(500)
    return users


@api.post("/users/promote")
async def promote_user(payload: PromoteIn, user: dict = Depends(require_roles("admin"))):
    target = await db.users.find_one({"user_id": payload.user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    update = {"role": payload.role}
    if payload.department_id is not None:
        update["department_id"] = payload.department_id
    await db.users.update_one({"user_id": payload.user_id}, {"$set": update})
    await log_activity(user, "promoted", "user", payload.user_id, target["name"], {"role": payload.role})
    await add_notification(payload.user_id, "role_updated", f"You are now {payload.role.replace('_', ' ').title()}", "Your permissions have been updated.")
    return {"ok": True}


# Departments
@api.get("/departments")
async def list_departments(_: dict = Depends(get_current_user)):
    return await db.departments.find({}, {"_id": 0}).to_list(500)


@api.post("/departments")
async def create_department(payload: DepartmentIn, user: dict = Depends(require_roles("admin"))):
    doc = {
        "department_id": new_id("dep"),
        **payload.model_dump(),
        "created_at": iso(now_utc()),
    }
    await db.departments.insert_one(doc)
    await log_activity(user, "created", "department", doc["department_id"], doc["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@api.patch("/departments/{department_id}")
async def update_department(department_id: str, payload: DepartmentIn, user: dict = Depends(require_roles("admin"))):
    r = await db.departments.update_one({"department_id": department_id}, {"$set": payload.model_dump()})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"ok": True}


@api.delete("/departments/{department_id}")
async def delete_department(department_id: str, user: dict = Depends(require_roles("admin"))):
    await db.departments.delete_one({"department_id": department_id})
    return {"ok": True}


# Categories
@api.get("/categories")
async def list_categories(_: dict = Depends(get_current_user)):
    return await db.categories.find({}, {"_id": 0}).to_list(500)


@api.post("/categories")
async def create_category(payload: CategoryIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    doc = {"category_id": new_id("cat"), **payload.model_dump(), "created_at": iso(now_utc())}
    await db.categories.insert_one(doc)
    await log_activity(user, "created", "category", doc["category_id"], doc["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@api.delete("/categories/{category_id}")
async def delete_category(category_id: str, user: dict = Depends(require_roles("admin", "asset_manager"))):
    await db.categories.delete_one({"category_id": category_id})
    return {"ok": True}


# ============================================================
# ASSETS
# ============================================================
@api.get("/assets")
async def list_assets(
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    status_: Optional[str] = Query(None, alias="status"),
    department_id: Optional[str] = None,
    bookable: Optional[bool] = None,
    _: dict = Depends(get_current_user),
):
    query: dict = {}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"tag": {"$regex": q, "$options": "i"}},
            {"serial": {"$regex": q, "$options": "i"}},
        ]
    if category_id:
        query["category_id"] = category_id
    if status_:
        query["status"] = status_
    if department_id:
        query["department_id"] = department_id
    if bookable is not None:
        query["bookable"] = bookable
    return await db.assets.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)


@api.get("/assets/{asset_id}")
async def get_asset(asset_id: str, _: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    allocations = await db.allocations.find({"asset_id": asset_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    maintenance = await db.maintenance_requests.find({"asset_id": asset_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"asset": asset, "allocations": allocations, "maintenance": maintenance}


@api.post("/assets")
async def create_asset(payload: AssetIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    if await db.assets.find_one({"tag": payload.tag}):
        raise HTTPException(status_code=400, detail="Asset tag already exists")
    doc = {
        "asset_id": new_id("ast"),
        **payload.model_dump(),
        "status": "available",
        "current_holder_id": None,
        "created_by": user["user_id"],
        "created_at": iso(now_utc()),
    }
    await db.assets.insert_one(doc)
    await log_activity(user, "registered", "asset", doc["asset_id"], doc["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@api.patch("/assets/{asset_id}")
async def update_asset(asset_id: str, payload: AssetIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    r = await db.assets.update_one({"asset_id": asset_id}, {"$set": payload.model_dump()})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")
    await log_activity(user, "updated", "asset", asset_id, payload.name)
    return {"ok": True}


@api.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str, user: dict = Depends(require_roles("admin", "asset_manager"))):
    await db.assets.delete_one({"asset_id": asset_id})
    return {"ok": True}


# ============================================================
# ALLOCATION & TRANSFER
# ============================================================
@api.post("/allocations")
async def allocate_asset(payload: AllocateIn, user: dict = Depends(require_roles("admin", "asset_manager", "department_head"))):
    asset = await db.assets.find_one({"asset_id": payload.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if asset["status"] == "allocated" and asset.get("current_holder_id"):
        holder = await db.users.find_one({"user_id": asset["current_holder_id"]}, {"_id": 0, "password_hash": 0})
        raise HTTPException(status_code=409, detail={
            "message": "Asset already allocated. Use transfer flow.",
            "current_holder": clean_user(holder) if holder else None,
        })
    if asset["status"] in ("under_maintenance", "lost", "retired", "disposed"):
        raise HTTPException(status_code=400, detail=f"Cannot allocate asset in status: {asset['status']}")
    assignee = await db.users.find_one({"user_id": payload.assignee_user_id}, {"_id": 0, "password_hash": 0})
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    alloc = {
        "allocation_id": new_id("alc"),
        "asset_id": payload.asset_id,
        "asset_name": asset["name"],
        "assignee_user_id": payload.assignee_user_id,
        "assignee_name": assignee["name"],
        "expected_return": payload.expected_return,
        "notes": payload.notes,
        "state": "active",
        "allocated_by": user["user_id"],
        "created_at": iso(now_utc()),
        "returned_at": None,
    }
    await db.allocations.insert_one(alloc)
    await db.assets.update_one({"asset_id": payload.asset_id}, {"$set": {"status": "allocated", "current_holder_id": payload.assignee_user_id}})
    await log_activity(user, "allocated", "asset", asset["asset_id"], asset["name"], {"assignee": assignee["name"]})
    await add_notification(payload.assignee_user_id, "asset_assigned", f"Asset '{asset['name']}' assigned to you", asset.get("tag", ""))
    return {k: v for k, v in alloc.items() if k != "_id"}


@api.post("/allocations/return")
async def return_asset(payload: ReturnIn, user: dict = Depends(get_current_user)):
    alloc = await db.allocations.find_one({"allocation_id": payload.allocation_id})
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")
    if alloc["state"] != "active":
        raise HTTPException(status_code=400, detail="Allocation already closed")
    # Employees can return their own; managers can return anyone's
    if user["role"] not in ("admin", "asset_manager", "department_head") and alloc["assignee_user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.allocations.update_one({"allocation_id": payload.allocation_id}, {"$set": {
        "state": "returned",
        "returned_at": iso(now_utc()),
        "condition_notes": payload.condition_notes,
    }})
    await db.assets.update_one({"asset_id": alloc["asset_id"]}, {"$set": {"status": "available", "current_holder_id": None}})
    await log_activity(user, "returned", "asset", alloc["asset_id"], alloc["asset_name"])
    return {"ok": True}


@api.get("/allocations")
async def list_allocations(state: Optional[str] = None, _: dict = Depends(get_current_user)):
    q = {"state": state} if state else {}
    return await db.allocations.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


@api.post("/transfers")
async def request_transfer(payload: TransferRequestIn, user: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": payload.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    to_user = await db.users.find_one({"user_id": payload.to_user_id}, {"_id": 0, "password_hash": 0})
    if not to_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    doc = {
        "transfer_id": new_id("trf"),
        "asset_id": payload.asset_id,
        "asset_name": asset["name"],
        "from_user_id": asset.get("current_holder_id"),
        "to_user_id": payload.to_user_id,
        "to_user_name": to_user["name"],
        "requested_by": user["user_id"],
        "reason": payload.reason,
        "status": "requested",
        "created_at": iso(now_utc()),
        "reviewed_at": None,
    }
    await db.transfers.insert_one(doc)
    await log_activity(user, "requested_transfer", "asset", asset["asset_id"], asset["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@api.get("/transfers")
async def list_transfers(status_: Optional[str] = Query(None, alias="status"), _: dict = Depends(get_current_user)):
    q = {"status": status_} if status_ else {}
    return await db.transfers.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


@api.post("/transfers/{transfer_id}/approve")
async def approve_transfer(transfer_id: str, user: dict = Depends(require_roles("admin", "asset_manager", "department_head"))):
    t = await db.transfers.find_one({"transfer_id": transfer_id})
    if not t or t["status"] != "requested":
        raise HTTPException(status_code=400, detail="Invalid transfer")
    # Close existing active allocation
    await db.allocations.update_many({"asset_id": t["asset_id"], "state": "active"}, {"$set": {"state": "transferred", "returned_at": iso(now_utc())}})
    # Create new allocation
    assignee = await db.users.find_one({"user_id": t["to_user_id"]}, {"_id": 0, "password_hash": 0})
    alloc = {
        "allocation_id": new_id("alc"),
        "asset_id": t["asset_id"],
        "asset_name": t["asset_name"],
        "assignee_user_id": t["to_user_id"],
        "assignee_name": assignee["name"] if assignee else "",
        "expected_return": None,
        "notes": f"Transferred from previous holder ({t.get('reason', '')})",
        "state": "active",
        "allocated_by": user["user_id"],
        "created_at": iso(now_utc()),
        "returned_at": None,
    }
    await db.allocations.insert_one(alloc)
    await db.assets.update_one({"asset_id": t["asset_id"]}, {"$set": {"status": "allocated", "current_holder_id": t["to_user_id"]}})
    await db.transfers.update_one({"transfer_id": transfer_id}, {"$set": {"status": "approved", "reviewed_at": iso(now_utc()), "reviewed_by": user["user_id"]}})
    await log_activity(user, "approved_transfer", "asset", t["asset_id"], t["asset_name"])
    await add_notification(t["to_user_id"], "transfer_approved", f"Transfer of '{t['asset_name']}' approved", "")
    return {"ok": True}


@api.post("/transfers/{transfer_id}/reject")
async def reject_transfer(transfer_id: str, user: dict = Depends(require_roles("admin", "asset_manager", "department_head"))):
    r = await db.transfers.update_one(
        {"transfer_id": transfer_id, "status": "requested"},
        {"$set": {"status": "rejected", "reviewed_at": iso(now_utc()), "reviewed_by": user["user_id"]}},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=400, detail="Invalid transfer")
    return {"ok": True}


# ============================================================
# RESOURCE BOOKING
# ============================================================
@api.get("/bookings")
async def list_bookings(asset_id: Optional[str] = None, _: dict = Depends(get_current_user)):
    q: dict = {}
    if asset_id:
        q["asset_id"] = asset_id
    return await db.bookings.find(q, {"_id": 0}).sort("start_at", 1).to_list(1000)


@api.post("/bookings")
async def create_booking(payload: BookingIn, user: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": payload.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not asset.get("bookable"):
        raise HTTPException(status_code=400, detail="Asset is not bookable")
    try:
        start = datetime.fromisoformat(payload.start_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(payload.end_at.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # booking_guard: check for overlaps (excluding cancelled)
    overlap = await db.bookings.find_one({
        "asset_id": payload.asset_id,
        "status": {"$in": ["upcoming", "ongoing"]},
        "start_at_dt": {"$lt": end},
        "end_at_dt": {"$gt": start},
    })
    if overlap:
        raise HTTPException(status_code=409, detail={
            "message": "Time slot conflicts with existing booking",
            "conflict": {"start": overlap["start_at"], "end": overlap["end_at"], "user": overlap.get("user_name")},
        })
    doc = {
        "booking_id": new_id("bkg"),
        "asset_id": payload.asset_id,
        "asset_name": asset["name"],
        "user_id": user["user_id"],
        "user_name": user["name"],
        "start_at": iso(start),
        "end_at": iso(end),
        "start_at_dt": start,
        "end_at_dt": end,
        "purpose": payload.purpose,
        "status": "upcoming",
        "created_at": iso(now_utc()),
    }
    await db.bookings.insert_one(doc)
    await log_activity(user, "booked", "asset", asset["asset_id"], asset["name"])
    await add_notification(user["user_id"], "booking_confirmed", f"Booking confirmed: {asset['name']}", f"{iso(start)} → {iso(end)}")
    out = {k: v for k, v in doc.items() if k not in ("_id", "start_at_dt", "end_at_dt")}
    return out


@api.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"booking_id": booking_id})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user["role"] not in ("admin", "asset_manager") and b["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.bookings.update_one({"booking_id": booking_id}, {"$set": {"status": "cancelled"}})
    await log_activity(user, "cancelled_booking", "asset", b["asset_id"], b["asset_name"])
    return {"ok": True}


# ============================================================
# MAINTENANCE
# ============================================================
@api.get("/maintenance")
async def list_maintenance(_: dict = Depends(get_current_user)):
    return await db.maintenance_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@api.post("/maintenance")
async def create_maintenance(payload: MaintenanceIn, user: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": payload.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    doc = {
        "request_id": new_id("mnt"),
        "asset_id": payload.asset_id,
        "asset_name": asset["name"],
        "raised_by": user["user_id"],
        "raised_by_name": user["name"],
        "issue": payload.issue,
        "priority": payload.priority,
        "photo_url": payload.photo_url,
        "status": "pending",
        "technician": "",
        "resolution_notes": "",
        "created_at": iso(now_utc()),
        "updated_at": iso(now_utc()),
    }
    await db.maintenance_requests.insert_one(doc)
    await log_activity(user, "raised_maintenance", "asset", asset["asset_id"], asset["name"], {"priority": payload.priority})
    return {k: v for k, v in doc.items() if k != "_id"}


@api.post("/maintenance/move")
async def move_maintenance(payload: MaintenanceMoveIn, user: dict = Depends(require_roles("admin", "asset_manager", "department_head"))):
    req = await db.maintenance_requests.find_one({"request_id": payload.request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    update = {"status": payload.to_status, "updated_at": iso(now_utc())}
    if payload.technician:
        update["technician"] = payload.technician
    if payload.resolution_notes:
        update["resolution_notes"] = payload.resolution_notes
    await db.maintenance_requests.update_one({"request_id": payload.request_id}, {"$set": update})

    # Side-effects: sync asset status
    if payload.to_status == "approved":
        await db.assets.update_one({"asset_id": req["asset_id"]}, {"$set": {"status": "under_maintenance"}})
    elif payload.to_status == "resolved":
        await db.assets.update_one({"asset_id": req["asset_id"]}, {"$set": {"status": "available"}})
    await log_activity(user, f"maintenance_{payload.to_status}", "asset", req["asset_id"], req["asset_name"])
    await add_notification(req["raised_by"], f"maintenance_{payload.to_status}", f"Maintenance {payload.to_status}: {req['asset_name']}", req["issue"])
    return {"ok": True}


# ============================================================
# DASHBOARD + ACTIVITY + NOTIFICATIONS
# ============================================================
@api.get("/dashboard/stats")
async def dashboard_stats(_: dict = Depends(get_current_user)):
    total = await db.assets.count_documents({})
    available = await db.assets.count_documents({"status": "available"})
    allocated = await db.assets.count_documents({"status": "allocated"})
    under_maintenance = await db.assets.count_documents({"status": "under_maintenance"})
    active_bookings = await db.bookings.count_documents({"status": {"$in": ["upcoming", "ongoing"]}})
    pending_transfers = await db.transfers.count_documents({"status": "requested"})
    # Overdue: allocations with expected_return < now and active
    now_iso = iso(now_utc())
    overdue = await db.allocations.count_documents({"state": "active", "expected_return": {"$ne": None, "$lt": now_iso}})
    upcoming_returns = await db.allocations.count_documents({"state": "active", "expected_return": {"$gt": now_iso}})
    return {
        "total": total,
        "available": available,
        "allocated": allocated,
        "under_maintenance": under_maintenance,
        "active_bookings": active_bookings,
        "pending_transfers": pending_transfers,
        "overdue": overdue,
        "upcoming_returns": upcoming_returns,
    }


@api.get("/activity")
async def activity_feed(limit: int = 50, kind: Optional[str] = None, _: dict = Depends(get_current_user)):
    q = {"kind": kind} if kind else {}
    return await db.activity_logs.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


@api.get("/notifications")
async def my_notifications(user: dict = Depends(get_current_user)):
    return await db.notifications.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)


@api.post("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user["user_id"]}, {"$set": {"read": True}})
    return {"ok": True}


# ============================================================
# FILE UPLOADS (Emergent object storage)
# ============================================================
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}


@api.post("/uploads")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ctype = file.content_type or "application/octet-stream"
    if ctype not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ctype}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    path = build_path(user["user_id"], file.filename or "upload", ctype)
    try:
        result = await asyncio.to_thread(put_object, path, data, ctype)
    except Exception as e:
        log.exception("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Storage upload failed")
    file_id = new_id("fil")
    await db.files.insert_one({
        "file_id": file_id,
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": ctype,
        "size": result.get("size", len(data)),
        "uploaded_by": user["user_id"],
        "is_deleted": False,
        "created_at": iso(now_utc()),
    })
    return {
        "file_id": file_id,
        "url": f"/api/uploads/{file_id}",
        "content_type": ctype,
        "size": result.get("size", len(data)),
        "filename": file.filename,
    }


@api.get("/uploads/{file_id}")
async def download_file(file_id: str, request: Request, auth: Optional[str] = None):
    """Download a file. Auth via httpOnly cookie (preferred) or ?auth=<jwt> query param
    for <img src> tags that can't send Authorization headers."""
    user = None
    # Try cookie/bearer via standard helper
    try:
        user = await get_current_user(request)
    except HTTPException:
        pass
    # Fallback: JWT via query param
    if not user and auth:
        try:
            payload = jwt.decode(auth, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") == "access":
                user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        except jwt.PyJWTError:
            pass
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rec = await db.files.find_one({"file_id": file_id, "is_deleted": False}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content, ctype = await asyncio.to_thread(get_object, rec["storage_path"])
    except Exception as e:
        log.exception("Download failed: %s", e)
        raise HTTPException(status_code=500, detail="Storage download failed")
    return FastAPIResponse(content=content, media_type=rec.get("content_type", ctype))


# ============================================================
# AUDIT CYCLES
# ============================================================
class AuditCycleIn(BaseModel):
    name: str
    department_id: Optional[str] = None
    location: Optional[str] = ""
    start_date: str  # ISO date
    end_date: str
    auditor_ids: List[str] = []


class AuditItemMark(BaseModel):
    result: Literal["verified", "missing", "damaged"]
    notes: Optional[str] = ""


@api.post("/audit/cycles")
async def create_audit_cycle(payload: AuditCycleIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    # Basic date sanity
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    cycle_id = new_id("adt")
    # snapshot in-scope assets
    query: dict = {"status": {"$nin": ["disposed", "retired"]}}
    if payload.department_id:
        query["department_id"] = payload.department_id
    if payload.location:
        query["location"] = {"$regex": payload.location, "$options": "i"}
    assets = await db.assets.find(query, {"_id": 0}).to_list(2000)
    cycle_doc = {
        "cycle_id": cycle_id,
        "name": payload.name,
        "department_id": payload.department_id,
        "location": payload.location,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "auditor_ids": payload.auditor_ids,
        "status": "in_progress",  # in_progress | closed
        "asset_count": len(assets),
        "created_by": user["user_id"],
        "created_at": iso(now_utc()),
        "closed_at": None,
    }
    await db.audit_cycles.insert_one(cycle_doc)
    if assets:
        items = [{
            "item_id": new_id("adi"),
            "cycle_id": cycle_id,
            "asset_id": a["asset_id"],
            "asset_tag": a["tag"],
            "asset_name": a["name"],
            "expected_location": a.get("location", ""),
            "result": None,  # pending | verified | missing | damaged
            "notes": "",
            "marked_by": None,
            "marked_at": None,
        } for a in assets]
        await db.audit_items.insert_many(items)
    await log_activity(user, "created_audit", "audit", cycle_id, payload.name)
    for aid in payload.auditor_ids:
        await add_notification(aid, "audit_assigned", f"You've been assigned to audit: {payload.name}", "")
    return {k: v for k, v in cycle_doc.items() if k != "_id"}


@api.get("/audit/cycles")
async def list_audit_cycles(_: dict = Depends(get_current_user)):
    cycles = await db.audit_cycles.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    # attach quick counts
    for c in cycles:
        pipeline = [
            {"$match": {"cycle_id": c["cycle_id"]}},
            {"$group": {"_id": "$result", "count": {"$sum": 1}}},
        ]
        counts = {"verified": 0, "missing": 0, "damaged": 0, "pending": 0}
        async for row in db.audit_items.aggregate(pipeline):
            key = row["_id"] or "pending"
            counts[key] = row["count"]
        c["counts"] = counts
    return cycles


@api.get("/audit/cycles/{cycle_id}")
async def get_audit_cycle(cycle_id: str, _: dict = Depends(get_current_user)):
    cycle = await db.audit_cycles.find_one({"cycle_id": cycle_id}, {"_id": 0})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    items = await db.audit_items.find({"cycle_id": cycle_id}, {"_id": 0}).to_list(2000)
    return {"cycle": cycle, "items": items}


@api.post("/audit/items/{item_id}/mark")
async def mark_audit_item(item_id: str, payload: AuditItemMark, user: dict = Depends(get_current_user)):
    item = await db.audit_items.find_one({"item_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    cycle = await db.audit_cycles.find_one({"cycle_id": item["cycle_id"]}, {"_id": 0})
    if cycle["status"] == "closed":
        raise HTTPException(status_code=400, detail="Cycle already closed")
    # RBAC: auditor assigned OR admin/asset_manager
    is_privileged = user["role"] in ("admin", "asset_manager")
    if not is_privileged and user["user_id"] not in cycle.get("auditor_ids", []):
        raise HTTPException(status_code=403, detail="Not assigned to this audit")
    await db.audit_items.update_one(
        {"item_id": item_id},
        {"$set": {
            "result": payload.result,
            "notes": payload.notes,
            "marked_by": user["user_id"],
            "marked_at": iso(now_utc()),
        }},
    )
    return {"ok": True}


@api.post("/audit/cycles/{cycle_id}/close")
async def close_audit_cycle(cycle_id: str, user: dict = Depends(require_roles("admin", "asset_manager"))):
    cycle = await db.audit_cycles.find_one({"cycle_id": cycle_id})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    if cycle["status"] == "closed":
        return {"ok": True, "message": "Already closed", "missing_updated": 0, "damaged_updated": 0}
    items = await db.audit_items.find({"cycle_id": cycle_id}, {"_id": 0}).to_list(2000)
    missing_ids = [i["asset_id"] for i in items if i.get("result") == "missing"]
    damaged_ids = [i["asset_id"] for i in items if i.get("result") == "damaged"]
    if missing_ids:
        await db.assets.update_many({"asset_id": {"$in": missing_ids}}, {"$set": {"status": "lost"}})
    if damaged_ids:
        await db.assets.update_many({"asset_id": {"$in": damaged_ids}}, {"$set": {"status": "under_maintenance"}})
    await db.audit_cycles.update_one(
        {"cycle_id": cycle_id},
        {"$set": {"status": "closed", "closed_at": iso(now_utc()), "closed_by": user["user_id"]}},
    )
    await log_activity(user, "closed_audit", "audit", cycle_id, cycle["name"], {
        "missing": len(missing_ids), "damaged": len(damaged_ids),
    })
    return {
        "ok": True,
        "missing_updated": len(missing_ids),
        "damaged_updated": len(damaged_ids),
    }


# ============================================================
# OVERDUE REMINDER (manual trigger)
# ============================================================
@api.post("/overdue/check")
async def trigger_overdue_check(user: dict = Depends(require_roles("admin", "asset_manager"))):
    await run_overdue_check_now(db, add_notification, send_email, overdue_email_html)
    return {"ok": True, "message": "Overdue check completed. See logs & notifications."}


# ============================================================
# STARTUP / SEED
# ============================================================
async def seed_data():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.assets.create_index("asset_id", unique=True)
    await db.assets.create_index("tag", unique=True)
    await db.bookings.create_index([("asset_id", 1), ("start_at_dt", 1)])
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)

    admin_email = os.environ["ADMIN_EMAIL"].lower()
    admin_password = os.environ["ADMIN_PASSWORD"]

    async def upsert_user(email, name, role, password):
        existing = await db.users.find_one({"email": email})
        if existing:
            if not verify_password(password, existing.get("password_hash", "")):
                await db.users.update_one({"email": email}, {"$set": {"password_hash": hash_password(password)}})
            return existing["user_id"]
        uid = new_id("usr")
        await db.users.insert_one({
            "user_id": uid, "email": email, "name": name,
            "password_hash": hash_password(password),
            "role": role, "department_id": None, "avatar": "",
            "auth_provider": "password", "created_at": iso(now_utc()),
        })
        return uid

    admin_id = await upsert_user(admin_email, "Admin", "admin", admin_password)
    manager_id = await upsert_user("manager@assetflow.io", "Priya Ramesh", "asset_manager", "manager123")
    head_id = await upsert_user("head@assetflow.io", "Marcus Chen", "department_head", "head123")
    emp_id = await upsert_user("employee@assetflow.io", "Ava Rodriguez", "employee", "employee123")

    # Departments
    if await db.departments.count_documents({}) == 0:
        depts = [
            {"department_id": "dep_engineering", "name": "Engineering", "head_user_id": head_id, "parent_id": None, "active": True, "created_at": iso(now_utc())},
            {"department_id": "dep_operations", "name": "Operations", "head_user_id": None, "parent_id": None, "active": True, "created_at": iso(now_utc())},
            {"department_id": "dep_facilities", "name": "Facilities", "head_user_id": None, "parent_id": None, "active": True, "created_at": iso(now_utc())},
        ]
        await db.departments.insert_many(depts)
        await db.users.update_one({"user_id": head_id}, {"$set": {"department_id": "dep_engineering"}})
        await db.users.update_one({"user_id": emp_id}, {"$set": {"department_id": "dep_engineering"}})

    # Categories
    if await db.categories.count_documents({}) == 0:
        cats = [
            {"category_id": "cat_laptops", "name": "Laptops", "icon": "laptop", "custom_fields": ["cpu", "ram", "storage"], "created_at": iso(now_utc())},
            {"category_id": "cat_monitors", "name": "Monitors", "icon": "monitor", "custom_fields": ["size", "resolution"], "created_at": iso(now_utc())},
            {"category_id": "cat_rooms", "name": "Meeting Rooms", "icon": "door-open", "custom_fields": ["capacity"], "created_at": iso(now_utc())},
            {"category_id": "cat_projectors", "name": "Projectors", "icon": "projector", "custom_fields": ["lumens"], "created_at": iso(now_utc())},
            {"category_id": "cat_vehicles", "name": "Vehicles", "icon": "car", "custom_fields": ["plate", "fuel"], "created_at": iso(now_utc())},
        ]
        await db.categories.insert_many(cats)

    # Assets
    if await db.assets.count_documents({}) == 0:
        assets = [
            {"asset_id": new_id("ast"), "name": "MacBook Pro 16\" M3", "tag": "AF-LP-001", "serial": "MBP16-9F2E", "category_id": "cat_laptops", "department_id": "dep_engineering", "location": "HQ / Floor 3 / Locker A1", "condition": "new", "status": "available", "current_holder_id": None, "bookable": False, "photo_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800", "notes": "Assigned pool", "acquisition_cost": 2999, "acquisition_date": "2025-01-15", "custom_data": {"cpu": "M3 Pro", "ram": "32GB", "storage": "1TB"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Dell XPS 15", "tag": "AF-LP-002", "serial": "XPS15-C3A1", "category_id": "cat_laptops", "department_id": "dep_engineering", "location": "HQ / Floor 3", "condition": "good", "status": "allocated", "current_holder_id": emp_id, "bookable": False, "photo_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800", "notes": "", "acquisition_cost": 1899, "acquisition_date": "2024-06-10", "custom_data": {"cpu": "i9", "ram": "32GB", "storage": "1TB"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "LG UltraFine 27\" 5K", "tag": "AF-MN-001", "serial": "LG27-5K-77", "category_id": "cat_monitors", "department_id": "dep_engineering", "location": "HQ / Floor 3", "condition": "good", "status": "available", "current_holder_id": None, "bookable": False, "photo_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800", "notes": "", "acquisition_cost": 1299, "acquisition_date": "2024-08-01", "custom_data": {"size": "27", "resolution": "5K"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Boardroom Alpha", "tag": "AF-RM-001", "serial": "", "category_id": "cat_rooms", "department_id": "dep_facilities", "location": "HQ / Floor 5", "condition": "good", "status": "available", "current_holder_id": None, "bookable": True, "photo_url": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=800", "notes": "Capacity 12", "acquisition_cost": 0, "acquisition_date": None, "custom_data": {"capacity": "12"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Sony VPL-VW295ES 4K Projector", "tag": "AF-PJ-001", "serial": "SNY-PJ-4K-01", "category_id": "cat_projectors", "department_id": "dep_facilities", "location": "HQ / Floor 5 / AV Locker", "condition": "good", "status": "available", "current_holder_id": None, "bookable": True, "photo_url": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800", "notes": "", "acquisition_cost": 4500, "acquisition_date": "2024-02-14", "custom_data": {"lumens": "1500"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Ford Transit Van", "tag": "AF-VH-001", "serial": "VIN-1FTNS2EW", "category_id": "cat_vehicles", "department_id": "dep_operations", "location": "Depot / Bay 2", "condition": "good", "status": "under_maintenance", "current_holder_id": None, "bookable": True, "photo_url": "https://images.unsplash.com/photo-1568844293986-8d0400bd4745?w=800", "notes": "Oil change in progress", "acquisition_cost": 32000, "acquisition_date": "2023-11-20", "custom_data": {"plate": "8XT-2210", "fuel": "diesel"}, "created_at": iso(now_utc())},
        ]
        await db.assets.insert_many(assets)
        # Seed an active allocation for the XPS
        xps = next(a for a in assets if a["tag"] == "AF-LP-002")
        await db.allocations.insert_one({
            "allocation_id": new_id("alc"), "asset_id": xps["asset_id"], "asset_name": xps["name"],
            "assignee_user_id": emp_id, "assignee_name": "Ava Rodriguez",
            "expected_return": iso(now_utc() + timedelta(days=14)), "notes": "Onboarding kit",
            "state": "active", "allocated_by": manager_id, "created_at": iso(now_utc()), "returned_at": None,
        })
        # Seed an overdue allocation
        van = next(a for a in assets if a["tag"] == "AF-VH-001")
        await db.allocations.insert_one({
            "allocation_id": new_id("alc"), "asset_id": van["asset_id"], "asset_name": van["name"],
            "assignee_user_id": head_id, "assignee_name": "Marcus Chen",
            "expected_return": iso(now_utc() - timedelta(days=3)), "notes": "Off-site delivery",
            "state": "returned", "allocated_by": manager_id,
            "created_at": iso(now_utc() - timedelta(days=10)),
            "returned_at": iso(now_utc() - timedelta(days=1)),
        })
        # Seed a maintenance request for the van
        await db.maintenance_requests.insert_one({
            "request_id": new_id("mnt"), "asset_id": van["asset_id"], "asset_name": van["name"],
            "raised_by": head_id, "raised_by_name": "Marcus Chen",
            "issue": "Engine oil light on. Service required.", "priority": "high",
            "photo_url": "", "status": "in_progress", "technician": "AutoCare Ltd.",
            "resolution_notes": "", "created_at": iso(now_utc() - timedelta(days=2)), "updated_at": iso(now_utc()),
        })
        # Seed some sample activity
        await db.activity_logs.insert_many([
            {"activity_id": new_id("act"), "actor_id": manager_id, "actor_name": "Priya Ramesh", "action": "registered", "kind": "asset", "target_id": xps["asset_id"], "target_name": xps["name"], "meta": {}, "created_at": iso(now_utc() - timedelta(hours=2))},
            {"activity_id": new_id("act"), "actor_id": manager_id, "actor_name": "Priya Ramesh", "action": "allocated", "kind": "asset", "target_id": xps["asset_id"], "target_name": xps["name"], "meta": {"assignee": "Ava Rodriguez"}, "created_at": iso(now_utc() - timedelta(hours=1))},
            {"activity_id": new_id("act"), "actor_id": head_id, "actor_name": "Marcus Chen", "action": "raised_maintenance", "kind": "asset", "target_id": van["asset_id"], "target_name": van["name"], "meta": {"priority": "high"}, "created_at": iso(now_utc() - timedelta(minutes=30))},
        ])

    log.info("Seed complete.")


@app.on_event("startup")
async def on_startup():
    try:
        await seed_data()
    except Exception as e:
        log.exception("Seed failed: %s", e)
    # init object storage (best-effort)
    try:
        await asyncio.to_thread(init_storage)
        log.info("Object storage initialized")
    except Exception as e:
        log.warning("Object storage init failed (uploads will 500): %s", e)
    # kick off overdue reminder background loop
    asyncio.create_task(overdue_reminder_loop(db, add_notification, send_email, overdue_email_html, interval_seconds=3600))
    log.info("Overdue reminder loop scheduled (hourly)")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()


# ---------- App wiring ----------
@api.get("/health")
async def health():
    return {"ok": True, "service": "assetflow", "time": iso(now_utc())}


app.include_router(api)

_frontend_url = os.environ.get("FRONTEND_URL", "").strip()
_cors_env = os.environ.get("CORS_ORIGINS", "*").strip()
if _cors_env == "*":
    # Credentials + wildcard is invalid; whitelist just the frontend origin.
    _allow_origins = [_frontend_url] if _frontend_url else ["*"]
    _allow_credentials = bool(_frontend_url)
else:
    _allow_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
    _allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_credentials,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
