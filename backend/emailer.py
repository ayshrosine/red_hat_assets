"""Resend email helper — non-blocking sends."""
import os
import asyncio
import logging
import resend

log = logging.getLogger("assetflow.emailer")

_key = os.environ.get("RESEND_API_KEY", "")
if _key:
    resend.api_key = _key
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")


async def send_email(to: str, subject: str, html: str) -> dict:
    if not _key:
        log.warning("RESEND_API_KEY missing — email not sent to %s", to)
        return {"skipped": True}
    params = {"from": SENDER_EMAIL, "to": [to], "subject": subject, "html": html}
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        log.info("Email sent to %s (id=%s)", to, result.get("id"))
        return result
    except Exception as e:
        log.error("Email send failed to %s: %s", to, e)
        return {"error": str(e)}


def overdue_email_html(user_name: str, asset_name: str, tag: str, days_overdue: int) -> str:
    return f"""
    <table width="100%" style="font-family:Arial,sans-serif;background:#050505;color:#fff;padding:24px">
      <tr><td>
        <div style="max-width:520px;margin:0 auto;background:#0e0e0e;border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:24px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px">
            <div style="width:20px;height:20px;background:linear-gradient(135deg,#00FF94,#00E5FF);border-radius:4px"></div>
            <strong style="letter-spacing:-0.02em">AssetFlow</strong>
          </div>
          <h2 style="color:#FF3366;margin:0 0 8px 0;font-weight:500;letter-spacing:-0.02em">Overdue return</h2>
          <p style="color:#a1a1aa;margin:0 0 16px 0">Hi {user_name},</p>
          <p style="color:#e4e4e7;margin:0 0 16px 0">
            The asset <strong style="color:#fff">{asset_name}</strong>
            (<span style="font-family:'JetBrains Mono',monospace;color:#a1a1aa">{tag}</span>)
            is <strong style="color:#FF3366">{days_overdue} day{'s' if days_overdue != 1 else ''}</strong> past its expected return date.
          </p>
          <p style="color:#e4e4e7;margin:0 0 24px 0">Please return it or update the return date in AssetFlow.</p>
          <p style="color:#71717a;font-size:12px;margin:24px 0 0 0;border-top:1px solid rgba(255,255,255,0.08);padding-top:16px">
            This is an automated reminder from AssetFlow.
          </p>
        </div>
      </td></tr>
    </table>
    """
