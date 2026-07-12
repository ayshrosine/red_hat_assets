"""Maintenance routes: Kanban state transitions with asset-status sync."""
from fastapi import APIRouter, Depends, HTTPException

from deps import (
    db, iso, now_utc, new_id,
    get_current_user, require_roles, log_activity, add_notification,
    MaintenanceIn, MaintenanceMoveIn,
)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("")
async def list_maintenance(_: dict = Depends(get_current_user)):
    return await db.maintenance_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.post("")
async def create_maintenance(payload: MaintenanceIn, user: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": payload.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    doc = {
        "request_id": new_id("mnt"),
        "asset_id": payload.asset_id, "asset_name": asset["name"],
        "raised_by": user["user_id"], "raised_by_name": user["name"],
        "issue": payload.issue, "priority": payload.priority,
        "photo_url": payload.photo_url,
        "status": "pending", "technician": "", "resolution_notes": "",
        "created_at": iso(now_utc()), "updated_at": iso(now_utc()),
    }
    await db.maintenance_requests.insert_one(doc)
    await log_activity(user, "raised_maintenance", "asset", asset["asset_id"], asset["name"], {"priority": payload.priority})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.post("/move")
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

    if payload.to_status == "approved":
        await db.assets.update_one({"asset_id": req["asset_id"]}, {"$set": {"status": "under_maintenance"}})
    elif payload.to_status == "resolved":
        await db.assets.update_one({"asset_id": req["asset_id"]}, {"$set": {"status": "available"}})
    await log_activity(user, f"maintenance_{payload.to_status}", "asset", req["asset_id"], req["asset_name"])
    await add_notification(req["raised_by"], f"maintenance_{payload.to_status}", f"Maintenance {payload.to_status}: {req['asset_name']}", req["issue"])
    return {"ok": True}
