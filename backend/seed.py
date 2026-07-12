"""Seed initial data: admin + demo users, departments, categories, sample assets."""
import os
import logging
from datetime import timedelta

from deps import db, iso, now_utc, new_id, hash_password, verify_password

log = logging.getLogger("assetflow.seed")


async def _upsert_user(email: str, name: str, role: str, password: str) -> str:
    existing = await db.users.find_one({"email": email})
    if existing:
        if not verify_password(password, existing.get("password_hash", "")):
            await db.users.update_one({"email": email}, {"$set": {"password_hash": hash_password(password)}})
        return existing["user_id"]
    uid = new_id("usr")
    await db.users.insert_one({
        "user_id": uid, "email": email, "name": name,
        "password_hash": hash_password(password),
        "role": role, "department_id": None, "avatar": "",
        "auth_provider": "password", "created_at": iso(now_utc()),
    })
    return uid


async def seed_data():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.assets.create_index("asset_id", unique=True)
    await db.assets.create_index("tag", unique=True)
    await db.bookings.create_index([("asset_id", 1), ("start_at_dt", 1)])
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)

    admin_email = os.environ["ADMIN_EMAIL"].lower()
    admin_password = os.environ["ADMIN_PASSWORD"]

    admin_id = await _upsert_user(admin_email, "Admin", "admin", admin_password)
    manager_id = await _upsert_user("manager@assetflow.io", "Priya Ramesh", "asset_manager", "manager123")
    head_id = await _upsert_user("head@assetflow.io", "Marcus Chen", "department_head", "head123")
    emp_id = await _upsert_user("employee@assetflow.io", "Ava Rodriguez", "employee", "employee123")

    if await db.departments.count_documents({}) == 0:
        depts = [
            {"department_id": "dep_engineering", "name": "Engineering", "head_user_id": head_id, "parent_id": None, "active": True, "created_at": iso(now_utc())},
            {"department_id": "dep_operations", "name": "Operations", "head_user_id": None, "parent_id": None, "active": True, "created_at": iso(now_utc())},
            {"department_id": "dep_facilities", "name": "Facilities", "head_user_id": None, "parent_id": None, "active": True, "created_at": iso(now_utc())},
        ]
        await db.departments.insert_many(depts)
        await db.users.update_one({"user_id": head_id}, {"$set": {"department_id": "dep_engineering"}})
        await db.users.update_one({"user_id": emp_id}, {"$set": {"department_id": "dep_engineering"}})

    if await db.categories.count_documents({}) == 0:
        cats = [
            {"category_id": "cat_laptops", "name": "Laptops", "icon": "laptop", "custom_fields": ["cpu", "ram", "storage"], "created_at": iso(now_utc())},
            {"category_id": "cat_monitors", "name": "Monitors", "icon": "monitor", "custom_fields": ["size", "resolution"], "created_at": iso(now_utc())},
            {"category_id": "cat_rooms", "name": "Meeting Rooms", "icon": "door-open", "custom_fields": ["capacity"], "created_at": iso(now_utc())},
            {"category_id": "cat_projectors", "name": "Projectors", "icon": "projector", "custom_fields": ["lumens"], "created_at": iso(now_utc())},
            {"category_id": "cat_vehicles", "name": "Vehicles", "icon": "car", "custom_fields": ["plate", "fuel"], "created_at": iso(now_utc())},
        ]
        await db.categories.insert_many(cats)

    if await db.assets.count_documents({}) == 0:
        assets = [
            {"asset_id": new_id("ast"), "name": "MacBook Pro 16\" M3", "tag": "AF-LP-001", "serial": "MBP16-9F2E", "category_id": "cat_laptops", "department_id": "dep_engineering", "location": "HQ / Floor 3 / Locker A1", "condition": "new", "status": "available", "current_holder_id": None, "bookable": False, "photo_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800", "photo_urls": [], "doc_urls": [], "notes": "Assigned pool", "acquisition_cost": 2999, "acquisition_date": "2025-01-15", "custom_data": {"cpu": "M3 Pro", "ram": "32GB", "storage": "1TB"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Dell XPS 15", "tag": "AF-LP-002", "serial": "XPS15-C3A1", "category_id": "cat_laptops", "department_id": "dep_engineering", "location": "HQ / Floor 3", "condition": "good", "status": "allocated", "current_holder_id": emp_id, "bookable": False, "photo_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800", "photo_urls": [], "doc_urls": [], "notes": "", "acquisition_cost": 1899, "acquisition_date": "2024-06-10", "custom_data": {"cpu": "i9", "ram": "32GB", "storage": "1TB"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "LG UltraFine 27\" 5K", "tag": "AF-MN-001", "serial": "LG27-5K-77", "category_id": "cat_monitors", "department_id": "dep_engineering", "location": "HQ / Floor 3", "condition": "good", "status": "available", "current_holder_id": None, "bookable": False, "photo_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800", "photo_urls": [], "doc_urls": [], "notes": "", "acquisition_cost": 1299, "acquisition_date": "2024-08-01", "custom_data": {"size": "27", "resolution": "5K"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Boardroom Alpha", "tag": "AF-RM-001", "serial": "", "category_id": "cat_rooms", "department_id": "dep_facilities", "location": "HQ / Floor 5", "condition": "good", "status": "available", "current_holder_id": None, "bookable": True, "photo_url": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=800", "photo_urls": [], "doc_urls": [], "notes": "Capacity 12", "acquisition_cost": 0, "acquisition_date": None, "custom_data": {"capacity": "12"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Sony VPL-VW295ES 4K Projector", "tag": "AF-PJ-001", "serial": "SNY-PJ-4K-01", "category_id": "cat_projectors", "department_id": "dep_facilities", "location": "HQ / Floor 5 / AV Locker", "condition": "good", "status": "available", "current_holder_id": None, "bookable": True, "photo_url": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800", "photo_urls": [], "doc_urls": [], "notes": "", "acquisition_cost": 4500, "acquisition_date": "2024-02-14", "custom_data": {"lumens": "1500"}, "created_at": iso(now_utc())},
            {"asset_id": new_id("ast"), "name": "Ford Transit Van", "tag": "AF-VH-001", "serial": "VIN-1FTNS2EW", "category_id": "cat_vehicles", "department_id": "dep_operations", "location": "Depot / Bay 2", "condition": "good", "status": "under_maintenance", "current_holder_id": None, "bookable": True, "photo_url": "https://images.unsplash.com/photo-1568844293986-8d0400bd4745?w=800", "photo_urls": [], "doc_urls": [], "notes": "Oil change in progress", "acquisition_cost": 32000, "acquisition_date": "2023-11-20", "custom_data": {"plate": "8XT-2210", "fuel": "diesel"}, "created_at": iso(now_utc())},
        ]
        await db.assets.insert_many(assets)
        xps = next(a for a in assets if a["tag"] == "AF-LP-002")
        van = next(a for a in assets if a["tag"] == "AF-VH-001")
        await db.allocations.insert_one({
            "allocation_id": new_id("alc"), "asset_id": xps["asset_id"], "asset_name": xps["name"],
            "assignee_user_id": emp_id, "assignee_name": "Ava Rodriguez",
            "expected_return": iso(now_utc() + timedelta(days=14)), "notes": "Onboarding kit",
            "state": "active", "allocated_by": manager_id, "created_at": iso(now_utc()), "returned_at": None,
        })
        await db.allocations.insert_one({
            "allocation_id": new_id("alc"), "asset_id": van["asset_id"], "asset_name": van["name"],
            "assignee_user_id": head_id, "assignee_name": "Marcus Chen",
            "expected_return": iso(now_utc() - timedelta(days=3)), "notes": "Off-site delivery",
            "state": "returned", "allocated_by": manager_id,
            "created_at": iso(now_utc() - timedelta(days=10)),
            "returned_at": iso(now_utc() - timedelta(days=1)),
        })
        await db.maintenance_requests.insert_one({
            "request_id": new_id("mnt"), "asset_id": van["asset_id"], "asset_name": van["name"],
            "raised_by": head_id, "raised_by_name": "Marcus Chen",
            "issue": "Engine oil light on. Service required.", "priority": "high",
            "photo_url": "", "status": "in_progress", "technician": "AutoCare Ltd.",
            "resolution_notes": "", "created_at": iso(now_utc() - timedelta(days=2)), "updated_at": iso(now_utc()),
        })
        await db.activity_logs.insert_many([
            {"activity_id": new_id("act"), "actor_id": manager_id, "actor_name": "Priya Ramesh", "action": "registered", "kind": "asset", "target_id": xps["asset_id"], "target_name": xps["name"], "meta": {}, "created_at": iso(now_utc() - timedelta(hours=2))},
            {"activity_id": new_id("act"), "actor_id": manager_id, "actor_name": "Priya Ramesh", "action": "allocated", "kind": "asset", "target_id": xps["asset_id"], "target_name": xps["name"], "meta": {"assignee": "Ava Rodriguez"}, "created_at": iso(now_utc() - timedelta(hours=1))},
            {"activity_id": new_id("act"), "actor_id": head_id, "actor_name": "Marcus Chen", "action": "raised_maintenance", "kind": "asset", "target_id": van["asset_id"], "target_name": van["name"], "meta": {"priority": "high"}, "created_at": iso(now_utc() - timedelta(minutes=30))},
        ])

    log.info("Seed complete.")
