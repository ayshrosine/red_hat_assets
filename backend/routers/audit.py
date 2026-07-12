"""Audit cycle routes."""
from fastapi import APIRouter, Depends, HTTPException

from deps import (
    db, iso, now_utc, new_id,
    get_current_user, require_roles, log_activity, add_notification,
    AuditCycleIn, AuditItemMark,
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/cycles")
async def create_audit_cycle(payload: AuditCycleIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    cycle_id = new_id("adt")
    query: dict = {"status": {"$nin": ["disposed", "retired"]}}
    if payload.department_id:
        query["department_id"] = payload.department_id
    if payload.location:
        query["location"] = {"$regex": payload.location, "$options": "i"}
    assets = await db.assets.find(query, {"_id": 0}).to_list(2000)
    cycle_doc = {
        "cycle_id": cycle_id, "name": payload.name,
        "department_id": payload.department_id, "location": payload.location,
        "start_date": payload.start_date, "end_date": payload.end_date,
        "auditor_ids": payload.auditor_ids,
        "status": "in_progress",
        "asset_count": len(assets),
        "created_by": user["user_id"], "created_at": iso(now_utc()),
        "closed_at": None,
    }
    await db.audit_cycles.insert_one(cycle_doc)
    if assets:
        items = [{
            "item_id": new_id("adi"),
            "cycle_id": cycle_id, "asset_id": a["asset_id"],
            "asset_tag": a["tag"], "asset_name": a["name"],
            "expected_location": a.get("location", ""),
            "result": None, "notes": "", "marked_by": None, "marked_at": None,
        } for a in assets]
        await db.audit_items.insert_many(items)
    await log_activity(user, "created_audit", "audit", cycle_id, payload.name)
    for aid in payload.auditor_ids:
        await add_notification(aid, "audit_assigned", f"You've been assigned to audit: {payload.name}", "")
    return {k: v for k, v in cycle_doc.items() if k != "_id"}


@router.get("/cycles")
async def list_audit_cycles(_: dict = Depends(get_current_user)):
    cycles = await db.audit_cycles.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
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


@router.get("/cycles/{cycle_id}")
async def get_audit_cycle(cycle_id: str, _: dict = Depends(get_current_user)):
    cycle = await db.audit_cycles.find_one({"cycle_id": cycle_id}, {"_id": 0})
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    items = await db.audit_items.find({"cycle_id": cycle_id}, {"_id": 0}).to_list(2000)
    return {"cycle": cycle, "items": items}


@router.post("/items/{item_id}/mark")
async def mark_audit_item(item_id: str, payload: AuditItemMark, user: dict = Depends(get_current_user)):
    item = await db.audit_items.find_one({"item_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    cycle = await db.audit_cycles.find_one({"cycle_id": item["cycle_id"]}, {"_id": 0})
    if cycle["status"] == "closed":
        raise HTTPException(status_code=400, detail="Cycle already closed")
    if user["role"] not in ("admin", "asset_manager") and user["user_id"] not in cycle.get("auditor_ids", []):
        raise HTTPException(status_code=403, detail="Not assigned to this audit")
    await db.audit_items.update_one(
        {"item_id": item_id},
        {"$set": {"result": payload.result, "notes": payload.notes, "marked_by": user["user_id"], "marked_at": iso(now_utc())}},
    )
    return {"ok": True}


@router.post("/cycles/{cycle_id}/close")
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
    return {"ok": True, "missing_updated": len(missing_ids), "damaged_updated": len(damaged_ids)}
