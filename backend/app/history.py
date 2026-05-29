"""Supabase-backed chat history persistence keyed by anonymous session id.

If SUPABASE_URL or SUPABASE_SERVICE_KEY is unset the module operates in a
no-op mode: every call returns an empty history and writes silently succeed,
so the rest of the app keeps working without persistence.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from app.config import settings

log = logging.getLogger(__name__)

# Browser-generated UUIDv4 (with dashes). Reject anything else so a bad client
# can't smuggle SQL-ish junk into the row key.
_SESSION_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def is_valid_session_id(session_id: str | None) -> bool:
    return bool(session_id and _SESSION_RE.match(session_id))


@lru_cache(maxsize=1)
def _client():
    if not (settings.supabase_url and settings.supabase_service_key):
        return None
    # Imported lazily so the app boots even before `supabase` is installed.
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_key)


def is_enabled() -> bool:
    return _client() is not None


def load_history(session_id: str) -> list[dict[str, Any]]:
    client = _client()
    if client is None or not is_valid_session_id(session_id):
        return []
    try:
        res = (
            client.table(settings.supabase_history_table)
            .select("role,text,sources,created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(settings.chat_history_limit)
            .execute()
        )
    except Exception:
        log.exception("supabase load_history failed")
        return []
    return [
        {
            "role": row["role"],
            "text": row["text"],
            "sources": row.get("sources") or [],
        }
        for row in (res.data or [])
    ]


def append_message(session_id: str, role: str, text: str, sources: list[str]) -> None:
    client = _client()
    if client is None or not is_valid_session_id(session_id):
        return
    try:
        client.table(settings.supabase_history_table).insert(
            {
                "session_id": session_id,
                "role": role,
                "text": text,
                "sources": sources,
            }
        ).execute()
    except Exception:
        log.exception("supabase append_message failed")


def clear_history(session_id: str) -> None:
    client = _client()
    if client is None or not is_valid_session_id(session_id):
        return
    try:
        client.table(settings.supabase_history_table).delete().eq(
            "session_id", session_id
        ).execute()
    except Exception:
        log.exception("supabase clear_history failed")
