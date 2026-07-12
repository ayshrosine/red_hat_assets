"""Asset routes: CRUD, search, detail with allocation + maintenance history."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from deps import (
    db, iso, now_utc, new_id,
    get_current_user, require_roles, log_activity,
    AssetIn,
)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("")
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


@router.get("/{asset_id}")
async def get_asset(asset_id: str, _: dict = Depends(get_current_user)):
    asset = await db.assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    allocations = await db.allocations.find({"asset_id": asset_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    maintenance = await db.maintenance_requests.find({"asset_id": asset_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"asset": asset, "allocations": allocations, "maintenance": maintenance}


@router.post("")
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


@router.patch("/{asset_id}")
async def update_asset(asset_id: str, payload: AssetIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    r = await db.assets.update_one({"asset_id": asset_id}, {"$set": payload.model_dump()})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")
    await log_activity(user, "updated", "asset", asset_id, payload.name)
    return {"ok": True}


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, user: dict = Depends(require_roles("admin", "asset_manager"))):
    await db.assets.delete_one({"asset_id": asset_id})
    return {"ok": True}
