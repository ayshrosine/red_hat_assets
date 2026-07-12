"""AssetFlow — thin FastAPI app bootstrap."""
import os
import asyncio
import logging

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from deps import client, db, log, add_notification
from storage import init_storage
from emailer import send_email, overdue_email_html
from scheduler import overdue_reminder_loop
from seed import seed_data
from routers import auth as auth_router
from routers import org as org_router
from routers import assets as assets_router
from routers import allocation as allocation_router
from routers import booking as booking_router
from routers import maintenance as maintenance_router
from routers import audit as audit_router
from routers import uploads as uploads_router
from routers import dashboard as dashboard_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AssetFlow API")

api = APIRouter(prefix="/api")
api.include_router(auth_router.router)
api.include_router(org_router.router)
api.include_router(assets_router.router)
api.include_router(allocation_router.router)
api.include_router(booking_router.router)
api.include_router(maintenance_router.router)
api.include_router(audit_router.router)
api.include_router(uploads_router.router)
api.include_router(dashboard_router.router)
app.include_router(api)

# ---------- CORS ----------
_frontend_url = os.environ.get("FRONTEND_URL", "").strip()
_cors_env = os.environ.get("CORS_ORIGINS", "*").strip()
if _cors_env == "*":
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


@app.on_event("startup")
async def on_startup():
    try:
        await seed_data()
    except Exception as e:
        log.exception("Seed failed: %s", e)
    try:
        await asyncio.to_thread(init_storage)
        log.info("Object storage initialized")
    except Exception as e:
        log.warning("Object storage init failed (uploads will 500): %s", e)
    asyncio.create_task(overdue_reminder_loop(db, add_notification, send_email, overdue_email_html, interval_seconds=3600))
    log.info("Overdue reminder loop scheduled (hourly)")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
