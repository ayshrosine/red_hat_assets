"""Dashboard stats, activity feed, notifications, health, manual overdue trigger."""
from typing import Optional
from fastapi import APIRouter, Depends

from deps import db, iso, now_utc, get_current_user, require_roles, add_notification
from emailer import send_email, overdue_email_html
from scheduler import run_overdue_check_now

router = APIRouter(tags=["dashboard"])


@router.get("/health")
async def health():
    return {"ok": True, "service": "assetflow", "time": iso(now_utc())}


@router.get("/dashboard/stats")
async def dashboard_stats(_: dict = Depends(get_current_user)):
    total = await db.assets.count_documents({})
    available = await db.assets.count_documents({"status": "available"})
    allocated = await db.assets.count_documents({"status": "allocated"})
    under_maintenance = await db.assets.count_documents({"status": "under_maintenance"})
    active_bookings = await db.bookings.count_documents({"status": {"$in": ["upcoming", "ongoing"]}})
    pending_transfers = await db.transfers.count_documents({"status": "requested"})
    now_iso = iso(now_utc())
    overdue = await db.allocations.count_documents({"state": "active", "expected_return": {"$ne": None, "$lt": now_iso}})
    upcoming_returns = await db.allocations.count_documents({"state": "active", "expected_return": {"$gt": now_iso}})
    return {
        "total": total, "available": available, "allocated": allocated,
        "under_maintenance": under_maintenance,
        "active_bookings": active_bookings, "pending_transfers": pending_transfers,
        "overdue": overdue, "upcoming_returns": upcoming_returns,
    }


@router.get("/activity")
async def activity_feed(limit: int = 50, kind: Optional[str] = None, _: dict = Depends(get_current_user)):
    q = {"kind": kind} if kind else {}
    return await db.activity_logs.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)


@router.get("/notifications")
async def my_notifications(user: dict = Depends(get_current_user)):
    return await db.notifications.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)


@router.post("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user["user_id"]}, {"$set": {"read": True}})
    return {"ok": True}


@router.post("/overdue/check")
async def trigger_overdue_check(user: dict = Depends(require_roles("admin", "asset_manager"))):
    await run_overdue_check_now(db, add_notification, send_email, overdue_email_html)
    return {"ok": True, "message": "Overdue check completed. See logs & notifications."}
