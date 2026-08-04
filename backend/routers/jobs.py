"""Jobs router for serverless task execution."""
import logging
from fastapi import APIRouter

from deps import db, add_notification
from emailer import send_email, overdue_email_html
from scheduler import run_overdue_check_now

log = logging.getLogger("assetflow.jobs")
router = APIRouter(prefix="/internal/jobs")


@router.post("/overdue-reminders")
async def run_overdue_reminders():
    """
    Run overdue reminder check as a one-shot job.
    This endpoint is designed for serverless execution (e.g., Knative Service).
    """
    try:
        await run_overdue_check_now(db, add_notification, send_email, overdue_email_html)
        return {"status": "completed", "message": "Overdue reminders processed"}
    except Exception as e:
        log.exception("Overdue reminder job failed: %s", e)
        return {"status": "failed", "error": str(e)}
