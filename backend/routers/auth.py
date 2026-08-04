"""Auth routes: register, login, logout, me, refresh, forgot/reset password, Google OAuth."""
import os
import secrets
import logging
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from deps import (
    db, JWT_SECRET, JWT_ALGORITHM, ACCESS_MIN,
    now_utc, iso, new_id, hash_password, verify_password,
    create_access_token, create_refresh_token, set_auth_cookies, clear_auth_cookies,
    clean_user, get_current_user,
    RegisterIn, LoginIn, ForgotIn, ResetIn, GoogleTokenIn,
)

log = logging.getLogger("assetflow.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterIn, response: Response):
    email = payload.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = new_id("usr")
    doc = {
        "user_id": user_id, "email": email, "name": payload.name.strip(),
        "password_hash": hash_password(payload.password),
        "role": "employee", "department_id": None, "avatar": "",
        "auth_provider": "password", "created_at": iso(now_utc()),
    }
    await db.users.insert_one(doc)
    set_auth_cookies(response, create_access_token(user_id, email), create_refresh_token(user_id))
    return clean_user(doc)


@router.post("/login")
async def login(payload: LoginIn, response: Response, request: Request):
    email = payload.email.lower().strip()
    ident = email
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
        if new_count >= 5:
            update["$set"]["locked_until"] = iso(now_utc() + timedelta(minutes=15))
        await db.login_attempts.update_one({"identifier": ident}, update, upsert=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await db.login_attempts.delete_one({"identifier": ident})
    set_auth_cookies(response, create_access_token(user["user_id"], email), create_refresh_token(user["user_id"]))
    return clean_user(user)


@router.post("/logout")
async def logout(response: Response, request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return clean_user(user)


@router.post("/refresh")
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
    is_dev = os.environ.get("ENV", "development") == "development"
    secure_cookie = not is_dev
    samesite_policy = "lax" if is_dev else "none"
    response.set_cookie("access_token", create_access_token(user["user_id"], user["email"]),
                        httponly=True, secure=secure_cookie, samesite=samesite_policy, max_age=ACCESS_MIN * 60, path="/")
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotIn):
    user = await db.users.find_one({"email": payload.email.lower().strip()})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token": token, "user_id": user["user_id"], "used": False,
            "expires_at": now_utc() + timedelta(hours=1), "created_at": iso(now_utc()),
        })
        log.info(f"[PWD-RESET] Reset link for {user['email']}: /reset-password?token={token}")
    return {"ok": True, "message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
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


@router.post("/google/token")
async def google_token(payload: GoogleTokenIn, response: Response):
    try:
        # Verify Google ID token
        google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")
        
        # Verify the ID token using Google's verification
        idinfo = id_token.verify_oauth2_token(
            payload.id_token, 
            google_requests.Request(), 
            google_client_id
        )
        
        # Get user info from verified token
        email = idinfo.get("email").lower().strip()
        name = idinfo.get("name", email.split("@")[0])
        picture = idinfo.get("picture", "")
        
        # Check if user exists
        existing = await db.users.find_one({"email": email})
        if existing:
            user_id = existing["user_id"]
            # Update user profile with latest Google data
            await db.users.update_one({"user_id": user_id}, {"$set": {
                "name": name,
                "avatar": picture,
            }})
        else:
            # Create new user
            user_id = new_id("usr")
            await db.users.insert_one({
                "user_id": user_id, 
                "email": email,
                "name": name,
                "avatar": picture,
                "role": "employee", 
                "department_id": None,
                "auth_provider": "google", 
                "created_at": iso(now_utc()),
            })
        
        # Create session and set auth cookies
        set_auth_cookies(response, create_access_token(user_id, email), create_refresh_token(user_id))
        
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        return clean_user(user)
        
    except Exception as e:
        log.error(f"Google token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google token")
