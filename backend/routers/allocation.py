"""Allocation & Transfer routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from deps import (
    db, iso, now_utc, new_id, clean_user,
    get_current_user, require_roles, log_activity, add_notification,
    AllocateIn, TransferRequestIn, ReturnIn,
)

router = APIRouter(tags=["allocation"])


@router.post("/allocations")
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
        "asset_id": payload.asset_id, "asset_name": asset["name"],
        "assignee_user_id": payload.assignee_user_id, "assignee_name": assignee["name"],
        "expected_return": payload.expected_return, "notes": payload.notes,
        "state": "active", "allocated_by": user["user_id"],
        "created_at": iso(now_utc()), "returned_at": None,
    }
    await db.allocations.insert_one(alloc)
    await db.assets.update_one({"asset_id": payload.asset_id}, {"$set": {"status": "allocated", "current_holder_id": payload.assignee_user_id}})
    await log_activity(user, "allocated", "asset", asset["asset_id"], asset["name"], {"assignee": assignee["name"]})
    await add_notification(payload.assignee_user_id, "asset_assigned", f"Asset '{asset['name']}' assigned to you", asset.get("tag", ""))
    return {k: v for k, v in alloc.items() if k != "_id"}


@router.post("/allocations/return")
async def return_asset(payload: ReturnIn, user: dict = Depends(get_current_user)):
    alloc = await db.allocations.find_one({"allocation_id": payload.allocation_id})
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")
    if alloc["state"] != "active":
        raise HTTPException(status_code=400, detail="Allocation already closed")
    if user["role"] not in ("admin", "asset_manager", "department_head") and alloc["assignee_user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.allocations.update_one({"allocation_id": payload.allocation_id}, {"$set": {
        "state": "returned", "returned_at": iso(now_utc()), "condition_notes": payload.condition_notes,
    }})
    await db.assets.update_one({"asset_id": alloc["asset_id"]}, {"$set": {"status": "available", "current_holder_id": None}})
    await log_activity(user, "returned", "asset", alloc["asset_id"], alloc["asset_name"])
    return {"ok": True}


@router.get("/allocations")
async def list_allocations(state: Optional[str] = None, _: dict = Depends(get_current_user)):
    q = {"state": state} if state else {}
    return await db.allocations.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.post("/transfers")
async def request_transfer(payload: TransferRequestIn, user: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": payload.asset_id})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    to_user = await db.users.find_one({"user_id": payload.to_user_id}, {"_id": 0, "password_hash": 0})
    if not to_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    doc = {
        "transfer_id": new_id("trf"),
        "asset_id": payload.asset_id, "asset_name": asset["name"],
        "from_user_id": asset.get("current_holder_id"),
        "to_user_id": payload.to_user_id, "to_user_name": to_user["name"],
        "requested_by": user["user_id"], "reason": payload.reason,
        "status": "requested",
        "created_at": iso(now_utc()), "reviewed_at": None,
    }
    await db.transfers.insert_one(doc)
    await log_activity(user, "requested_transfer", "asset", asset["asset_id"], asset["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@router.get("/transfers")
async def list_transfers(status_: Optional[str] = Query(None, alias="status"), _: dict = Depends(get_current_user)):
    q = {"status": status_} if status_ else {}
    return await db.transfers.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.post("/transfers/{transfer_id}/approve")
async def approve_transfer(transfer_id: str, user: dict = Depends(require_roles("admin", "asset_manager", "department_head"))):
    t = await db.transfers.find_one({"transfer_id": transfer_id})
    if not t or t["status"] != "requested":
        raise HTTPException(status_code=400, detail="Invalid transfer")
    await db.allocations.update_many({"asset_id": t["asset_id"], "state": "active"}, {"$set": {"state": "transferred", "returned_at": iso(now_utc())}})
    assignee = await db.users.find_one({"user_id": t["to_user_id"]}, {"_id": 0, "password_hash": 0})
    alloc = {
        "allocation_id": new_id("alc"),
        "asset_id": t["asset_id"], "asset_name": t["asset_name"],
        "assignee_user_id": t["to_user_id"],
        "assignee_name": assignee["name"] if assignee else "",
        "expected_return": None,
        "notes": f"Transferred from previous holder ({t.get('reason', '')})",
        "state": "active", "allocated_by": user["user_id"],
        "created_at": iso(now_utc()), "returned_at": None,
    }
    await db.allocations.insert_one(alloc)
    await db.assets.update_one({"asset_id": t["asset_id"]}, {"$set": {"status": "allocated", "current_holder_id": t["to_user_id"]}})
    await db.transfers.update_one({"transfer_id": transfer_id}, {"$set": {"status": "approved", "reviewed_at": iso(now_utc()), "reviewed_by": user["user_id"]}})
    await log_activity(user, "approved_transfer", "asset", t["asset_id"], t["asset_name"])
    await add_notification(t["to_user_id"], "transfer_approved", f"Transfer of '{t['asset_name']}' approved", "")
    return {"ok": True}


@router.post("/transfers/{transfer_id}/reject")
async def reject_transfer(transfer_id: str, user: dict = Depends(require_roles("admin", "asset_manager", "department_head"))):
    r = await db.transfers.update_one(
        {"transfer_id": transfer_id, "status": "requested"},
        {"$set": {"status": "rejected", "reviewed_at": iso(now_utc()), "reviewed_by": user["user_id"]}},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=400, detail="Invalid transfer")
    return {"ok": True}
