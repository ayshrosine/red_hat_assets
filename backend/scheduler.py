"""Background scheduler for overdue return reminders."""
import asyncio
import logging
from datetime import datetime, timezone

log = logging.getLogger("assetflow.scheduler")

# Track which allocations we've already emailed today (in-memory; resets on restart)
_notified_today: dict[str, str] = {}  # allocation_id -> "YYYY-MM-DD"


async def _check_overdue_once(db, add_notification, send_email, overdue_email_html):
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    now_iso = now.isoformat()
    cursor = db.allocations.find({"state": "active", "expected_return": {"$ne": None, "$lt": now_iso}})
    async for alloc in cursor:
        alloc_id = alloc["allocation_id"]
        if _notified_today.get(alloc_id) == today:
            continue  # already notified today
        user = await db.users.find_one({"user_id": alloc["assignee_user_id"]}, {"_id": 0})
        if not user:
            continue
        try:
            expected = alloc["expected_return"]
            if isinstance(expected, str):
                expected = datetime.fromisoformat(expected.replace("Z", "+00:00"))
            if expected.tzinfo is None:
                expected = expected.replace(tzinfo=timezone.utc)
            days_over = max(1, (now - expected).days)
        except Exception:
            days_over = 1
        # in-app notification
        await add_notification(
            user["user_id"],
            "overdue_return",
            f"Overdue: {alloc['asset_name']}",
            f"{days_over} day{'s' if days_over != 1 else ''} past expected return.",
            {"allocation_id": alloc_id, "days_overdue": days_over},
        )
        # email (best-effort)
        await send_email(
            user["email"],
            f"[AssetFlow] Overdue return: {alloc['asset_name']}",
            overdue_email_html(user["name"], alloc["asset_name"], alloc.get("asset_tag", ""), days_over),
        )
        _notified_today[alloc_id] = today
        log.info("Overdue notified: %s → %s", alloc_id, user["email"])


async def overdue_reminder_loop(db, add_notification, send_email, overdue_email_html, interval_seconds: int = 3600):
    """Runs forever, checking for overdue returns every `interval_seconds`."""
    # small initial delay so startup completes cleanly
    await asyncio.sleep(15)
    while True:
        try:
            await _check_overdue_once(db, add_notification, send_email, overdue_email_html)
        except Exception as e:
            log.exception("Overdue check failed: %s", e)
        await asyncio.sleep(interval_seconds)


async def run_overdue_check_now(db, add_notification, send_email, overdue_email_html):
    """Manual trigger (used by API endpoint)."""
    await _check_overdue_once(db, add_notification, send_email, overdue_email_html)
