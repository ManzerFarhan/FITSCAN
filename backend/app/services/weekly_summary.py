"""Weekly summary email to the Owner(s) (FR-ADM-13).

Sent through Resend's HTTP API (free Render instances block outbound SMTP). With no RESEND_API_KEY the summary can
still be previewed in the admin panel. Sent at most once per 7 days, by the hourly background loop, on or after
WEEKLY_SUMMARY_WEEKDAY at 09:00 IST. Aggregate numbers only - no client names, emails or results in the email.
"""
from __future__ import annotations

import html
from datetime import UTC, datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import DocumentStatus
from app.core.errors import AppError
from app.core.logging import get_logger
from app.db.models import AuditLog, Document, Parameter, User
from app.services.admin_service import READ_OK

log = get_logger("weekly_summary")
ACTION = "WEEKLY_SUMMARY_SENT"
IST = timezone(timedelta(hours=5, minutes=30))


def build(db: Session, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    start, prev = now - timedelta(days=7), now - timedelta(days=14)

    def count(model, col, a, b, *where):
        return db.scalar(select(func.count()).select_from(model).where(col >= a, col < b, *where)) or 0

    by_status = dict(db.execute(select(Document.status, func.count()).where(Document.uploaded_at >= start)
                                .group_by(Document.status)).all())
    ok = sum(by_status.get(s, 0) for s in READ_OK)
    failed = by_status.get(DocumentStatus.FAILED, 0)
    unrecognised = db.execute(
        select(func.lower(Parameter.name_raw), func.count()).join(Document, Document.id == Parameter.document_id)
        .where(Parameter.parameter_id.is_(None), Document.uploaded_at >= start)
        .group_by(func.lower(Parameter.name_raw)).order_by(func.count().desc()).limit(40)).all()
    # Email is a less private channel than the panel: only short, digit-free names (never a misread header line).
    unrecognised = [(n, c) for n, c in unrecognised if n and len(n) <= 40 and not any(ch.isdigit() for ch in n)][:10]
    return {
        "period": f"{start.astimezone(IST):%d %b} - {now.astimezone(IST):%d %b %Y}",
        "new_clients": count(User, User.created_at, start, now),
        "new_clients_prev": count(User, User.created_at, prev, start),
        "active_clients": count(User, User.last_login_at, start, now),
        "reports": count(Document, Document.uploaded_at, start, now),
        "reports_prev": count(Document, Document.uploaded_at, prev, start),
        "failed": failed,
        "read_success_rate": round(ok / (ok + failed), 3) if ok + failed else None,
        "total_clients": db.scalar(select(func.count()).select_from(User)) or 0,
        "unrecognised_tests": [{"name": n, "count": c} for n, c in unrecognised],
    }


def _delta(now: int, before: int) -> str:
    d = now - before
    return "same as last week" if d == 0 else f"{'+' if d > 0 else ''}{d} vs last week"


def render_html(s: dict, admin_url: str) -> str:
    rate = "-" if s["read_success_rate"] is None else f"{round(s['read_success_rate'] * 100)}%"
    tiles = [("New clients", s["new_clients"], _delta(s["new_clients"], s["new_clients_prev"])),
             ("Active clients", s["active_clients"], f"{s['total_clients']} clients in total"),
             ("Reports uploaded", s["reports"], _delta(s["reports"], s["reports_prev"])),
             ("Reading success", rate, f"{s['failed']} could not be read")]
    cells = "".join(
        f'<td style="padding:12px;border:1px solid #e2e8f0;border-radius:8px;width:25%">'
        f'<div style="font-size:11px;color:#64748b;text-transform:uppercase">{html.escape(t)}</div>'
        f'<div style="font-size:24px;font-weight:700;color:#0f172a">{v}</div>'
        f'<div style="font-size:12px;color:#64748b">{html.escape(sub)}</div></td>' for t, v, sub in tiles)
    names = "".join(f"<li>{html.escape(u['name'])} <span style='color:#64748b'>({u['count']}x)</span></li>"
                    for u in s["unrecognised_tests"]) or "<li>None - every test name was recognised.</li>"
    return f"""<div style="font-family:Inter,Segoe UI,Arial,sans-serif;max-width:640px;margin:auto;color:#0f172a">
<h2 style="color:#0f766e;margin-bottom:4px">FITSCAN weekly summary</h2>
<p style="color:#64748b;margin-top:0">{html.escape(s['period'])}</p>
<table cellspacing="8" style="width:100%"><tr>{cells}</tr></table>
<h3 style="margin-bottom:4px">Test names not recognised this week</h3>
<p style="color:#64748b;margin-top:0;font-size:13px">Candidates to add to the test dictionary.</p>
<ul style="font-size:14px">{names}</ul>
<p><a href="{html.escape(admin_url)}" style="background:#0f766e;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none">Open the admin panel</a></p>
<p style="color:#94a3b8;font-size:12px">Totals only - no client names or results are included in this email.</p></div>"""


def recipients() -> list[str]:
    return [e.strip() for e in get_settings().admin_emails.split(",") if e.strip()]


def send(db: Session, now: datetime | None = None) -> dict:
    s = get_settings()
    if not s.resend_api_key:
        raise AppError("EMAIL_NOT_CONFIGURED", "Email isn't set up yet: add RESEND_API_KEY on the server.", 400)
    to = recipients()
    if not to:
        raise AppError("NO_RECIPIENTS", "No owner email is set (ADMIN_EMAILS).", 400)
    summary = build(db, now)
    admin_url = s.frontend_origin.split(",")[0].strip().rstrip("/") + "/admin"
    r = httpx.post("https://api.resend.com/emails", timeout=20, headers={"Authorization": f"Bearer {s.resend_api_key}"},
                   json={"from": s.email_from, "to": to, "subject": f"FITSCAN weekly summary - {summary['period']}",
                         "html": render_html(summary, admin_url)})
    if r.status_code >= 300:
        log.warning("Weekly summary email failed: HTTP %s", r.status_code)
        raise AppError("EMAIL_FAILED", f"The email service refused the message (HTTP {r.status_code}). "
                                       "Check RESEND_API_KEY and that the sender/recipient are allowed.", 502)
    db.add(AuditLog(action=ACTION, entity="email", label=f"Weekly summary emailed to {len(to)} owner(s)",
                    at=now or datetime.now(UTC)))
    db.commit()
    return {"sent_to": len(to), "summary": summary}


def last_sent(db: Session) -> datetime | None:
    at = db.scalar(select(func.max(AuditLog.at)).where(AuditLog.action == ACTION))
    return at.replace(tzinfo=UTC) if at is not None and at.tzinfo is None else at


def maybe_send(db: Session, now: datetime | None = None) -> bool:
    """Called hourly. Sends when email is configured, it's the chosen weekday after 09:00 IST, and 6+ days passed."""
    s = get_settings()
    now = now or datetime.now(UTC)
    local = now.astimezone(IST)
    if not (s.resend_api_key and recipients()) or local.weekday() != s.weekly_summary_weekday or local.hour < 9:
        return False
    last = last_sent(db)
    if last is not None and now - last < timedelta(days=6):
        return False
    send(db, now)
    return True
