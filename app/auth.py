from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, status

from app.config import get_settings
from app.db import get_connection

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 10
SESSION_AUTH_KEY = "is_authenticated"
SESSION_ID_KEY = "session_id"


@dataclass(frozen=True)
class LoginState:
    ok: bool
    remaining_attempts: int
    error: str | None = None
    locked_until: str | None = None


def _now() -> datetime:
    return datetime.now()


def _format_locked_until(locked_until: datetime) -> str:
    return locked_until.strftime("%Y-%m-%d %H:%M")


def _ensure_session_id(request: Request) -> str:
    session_id = request.session.get(SESSION_ID_KEY)
    if session_id:
        return session_id
    session_id = secrets.token_urlsafe(16)
    request.session[SESSION_ID_KEY] = session_id
    return session_id


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def _attempt_key(request: Request) -> tuple[str, str]:
    return _client_ip(request), _ensure_session_id(request)


def authenticate_password(request: Request, password: str) -> LoginState:
    ip, session_id = _attempt_key(request)
    now = _now()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT fail_count, locked_until
            FROM auth_attempts
            WHERE ip = ? AND session_id = ?
            """,
            (ip, session_id),
        )
        row = cursor.fetchone()

        fail_count = row["fail_count"] if row else 0
        locked_until_text = row["locked_until"] if row else None
        locked_until = (
            datetime.strptime(locked_until_text, "%Y-%m-%d %H:%M:%S")
            if locked_until_text
            else None
        )

        if locked_until and now < locked_until:
            remaining = max(0, MAX_FAILED_ATTEMPTS - fail_count)
            return LoginState(
                ok=False,
                remaining_attempts=remaining,
                error="当前会话已锁定",
                locked_until=_format_locked_until(locked_until),
            )

        real_password = get_settings().app_password
        if password and real_password and secrets.compare_digest(password, real_password):
            cursor.execute(
                "DELETE FROM auth_attempts WHERE ip = ? AND session_id = ?",
                (ip, session_id),
            )
            conn.commit()
            request.session[SESSION_AUTH_KEY] = True
            return LoginState(ok=True, remaining_attempts=MAX_FAILED_ATTEMPTS)

        new_fail_count = fail_count + 1
        remaining = max(0, MAX_FAILED_ATTEMPTS - new_fail_count)
        new_locked_until = None
        if new_fail_count >= MAX_FAILED_ATTEMPTS:
            new_locked_until = now + timedelta(minutes=LOCK_MINUTES)

        cursor.execute(
            """
            INSERT INTO auth_attempts (ip, session_id, fail_count, locked_until, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(ip, session_id)
            DO UPDATE SET
                fail_count = excluded.fail_count,
                locked_until = excluded.locked_until,
                updated_at = excluded.updated_at
            """,
            (
                ip,
                session_id,
                new_fail_count,
                new_locked_until.strftime("%Y-%m-%d %H:%M:%S") if new_locked_until else None,
                now.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()

    if new_locked_until:
        return LoginState(
            ok=False,
            remaining_attempts=0,
            error="连续失败次数过多，已锁定",
            locked_until=_format_locked_until(new_locked_until),
        )

    return LoginState(ok=False, remaining_attempts=remaining, error="密码错误")


def logout(request: Request) -> None:
    request.session[SESSION_AUTH_KEY] = False


def require_auth(request: Request) -> None:
    if request.session.get(SESSION_AUTH_KEY):
        return
    raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})


def auth_dependency(request: Request) -> None:
    return require_auth(request)
