"""Shared dependencies for AssetFlow routers: db, auth, models, helpers."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal

import bcrypt
import jwt
from fastapi import HTTPException, Depends, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

# ---------- Config ----------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_MIN = 60 * 24
REFRESH_DAYS = 7

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

log = logging.getLogger("assetflow")

# ---------- Constants ----------
ROLES = ["admin", "asset_manager", "department_head", "employee"]
ASSET_STATUSES = ["available", "allocated", "reserved", "under_maintenance", "lost", "retired", "disposed"]


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
    payload = {"sub": user_id, "email": email, "type": "access", "exp": now_utc() + timedelta(minutes=ACCESS_MIN)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "type": "refresh", "exp": now_utc() + timedelta(days=REFRESH_DAYS)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_auth_cookies(response: Response, access: str, refresh: str):
    # Use secure=False for HTTP development, secure=True for HTTPS production
    is_dev = os.environ.get("ENV", "development") == "development"
    secure_cookie = not is_dev
    samesite_policy = "lax" if is_dev else "none"
    
    response.set_cookie("access_token", access, httponly=True, secure=secure_cookie, samesite=samesite_policy, max_age=ACCESS_MIN * 60, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=secure_cookie, samesite=samesite_policy, max_age=REFRESH_DAYS * 86400, path="/")


def clear_auth_cookies(response: Response):
    is_dev = os.environ.get("ENV", "development") == "development"
    samesite_policy = "lax" if is_dev else "none"
    
    response.delete_cookie("access_token", path="/", samesite=samesite_policy)
    response.delete_cookie("refresh_token", path="/", samesite=samesite_policy)
    response.delete_cookie("session_token", path="/", samesite=samesite_policy)


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
    token = request.cookies.get("access_token")
    if not token:
        auth_h = request.headers.get("Authorization", "")
        if auth_h.startswith("Bearer "):
            token = auth_h[7:]
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
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_h = request.headers.get("Authorization", "")
        if auth_h.startswith("Bearer "):
            session_token = auth_h[7:]
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
    await db.activity_logs.insert_one({
        "activity_id": new_id("act"),
        "actor_id": actor.get("user_id"),
        "actor_name": actor.get("name"),
        "action": action, "kind": kind,
        "target_id": target_id, "target_name": target_name,
        "meta": meta or {},
        "created_at": iso(now_utc()),
    })


async def add_notification(user_id: str, kind: str, title: str, body: str = "", meta: Optional[dict] = None):
    await db.notifications.insert_one({
        "notif_id": new_id("ntf"),
        "user_id": user_id, "kind": kind, "title": title, "body": body,
        "meta": meta or {}, "read": False,
        "created_at": iso(now_utc()),
    })


# ---------- Pydantic input models ----------
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


class GoogleTokenIn(BaseModel):
    id_token: str


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
    start_at: str
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


class AuditCycleIn(BaseModel):
    name: str
    department_id: Optional[str] = None
    location: Optional[str] = ""
    start_date: str
    end_date: str
    auditor_ids: List[str] = []


class AuditItemMark(BaseModel):
    result: Literal["verified", "missing", "damaged"]
    notes: Optional[str] = ""
