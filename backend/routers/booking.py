"""Resource booking routes with overlap validation."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from deps import (
    db, iso, now_utc, new_id,
    get_current_user, log_activity, add_notification,
    BookingIn,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("")
async def list_bookings(asset_id: Optional[str] = None, _: dict = Depends(get_current_user)):
    q: dict = {}
    if asset_id:
        q["asset_id"] = asset_id
    return await db.bookings.find(q, {"_id": 0, "start_at_dt": 0, "end_at_dt": 0}).sort("start_at", 1).to_list(1000)


@router.post("")
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
        "asset_id": payload.asset_id, "asset_name": asset["name"],
        "user_id": user["user_id"], "user_name": user["name"],
        "start_at": iso(start), "end_at": iso(end),
        "start_at_dt": start, "end_at_dt": end,
        "purpose": payload.purpose, "status": "upcoming",
        "created_at": iso(now_utc()),
    }
    await db.bookings.insert_one(doc)
    await log_activity(user, "booked", "asset", asset["asset_id"], asset["name"])
    await add_notification(user["user_id"], "booking_confirmed", f"Booking confirmed: {asset['name']}", f"{iso(start)} → {iso(end)}")
    return {k: v for k, v in doc.items() if k not in ("_id", "start_at_dt", "end_at_dt")}


@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"booking_id": booking_id})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user["role"] not in ("admin", "asset_manager") and b["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.bookings.update_one({"booking_id": booking_id}, {"$set": {"status": "cancelled"}})
    await log_activity(user, "cancelled_booking", "asset", b["asset_id"], b["asset_name"])
    return {"ok": True}
