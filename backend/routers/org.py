"""Organization routes: users, departments, categories."""
from fastapi import APIRouter, Depends, HTTPException

from deps import (
    db, iso, now_utc, new_id, clean_user,
    get_current_user, require_roles, log_activity, add_notification,
    PromoteIn, DepartmentIn, CategoryIn,
)

router = APIRouter(tags=["org"])


@router.get("/users")
async def list_users(user: dict = Depends(get_current_user)):
    return await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(500)


@router.post("/users/promote")
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


@router.get("/departments")
async def list_departments(_: dict = Depends(get_current_user)):
    return await db.departments.find({}, {"_id": 0}).to_list(500)


@router.post("/departments")
async def create_department(payload: DepartmentIn, user: dict = Depends(require_roles("admin"))):
    doc = {"department_id": new_id("dep"), **payload.model_dump(), "created_at": iso(now_utc())}
    await db.departments.insert_one(doc)
    await log_activity(user, "created", "department", doc["department_id"], doc["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/departments/{department_id}")
async def update_department(department_id: str, payload: DepartmentIn, user: dict = Depends(require_roles("admin"))):
    r = await db.departments.update_one({"department_id": department_id}, {"$set": payload.model_dump()})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"ok": True}


@router.delete("/departments/{department_id}")
async def delete_department(department_id: str, user: dict = Depends(require_roles("admin"))):
    await db.departments.delete_one({"department_id": department_id})
    return {"ok": True}


@router.get("/categories")
async def list_categories(_: dict = Depends(get_current_user)):
    return await db.categories.find({}, {"_id": 0}).to_list(500)


@router.post("/categories")
async def create_category(payload: CategoryIn, user: dict = Depends(require_roles("admin", "asset_manager"))):
    doc = {"category_id": new_id("cat"), **payload.model_dump(), "created_at": iso(now_utc())}
    await db.categories.insert_one(doc)
    await log_activity(user, "created", "category", doc["category_id"], doc["name"])
    return {k: v for k, v in doc.items() if k != "_id"}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user: dict = Depends(require_roles("admin", "asset_manager"))):
    await db.categories.delete_one({"category_id": category_id})
    return {"ok": True}
