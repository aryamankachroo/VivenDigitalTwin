import base64
from typing import Any

from googleapiclient.discovery import build

from auth import credentials_from_session


def _decode_part_body(part: dict[str, Any]) -> str:
    body = part.get("body") or {}
    data = body.get("data")
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_plain_text(payload: dict[str, Any]) -> str:
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        return _decode_part_body(payload)
    parts = payload.get("parts") or []
    for part in parts:
        nested = _extract_plain_text(part)
        if nested:
            return nested
        if part.get("mimeType") == "text/plain":
            text = _decode_part_body(part)
            if text:
                return text
    return ""


def _parse_message_to_email(message: dict, msg_id: str) -> dict:
    headers = message.get("payload", {}).get("headers", [])
    subject = next(
        (h["value"] for h in headers if h["name"].lower() == "subject"),
        "No Subject",
    )
    from_email = next(
        (h["value"] for h in headers if h["name"].lower() == "from"), "Unknown"
    )
    date = next(
        (h["value"] for h in headers if h["name"].lower() == "date"), "Unknown"
    )
    body = _extract_plain_text(message.get("payload", {}))
    return {
        "id": msg_id,
        "subject": subject,
        "from": from_email,
        "date": date,
        "body": body[:1000],
    }


def get_user_email(credentials_dict: dict) -> str:
    """Return the authenticated user's Gmail address."""
    try:
        credentials = credentials_from_session(credentials_dict)
        service = build("gmail", "v1", credentials=credentials)
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress", "")
    except Exception:
        return ""


def get_recent_emails(credentials_dict: dict, max_results: int = 20) -> list[dict]:
    """Return up to ``max_results`` inbox messages newest-first by ``internalDate``.

    Gmail's message list order does not always match the inbox UI (threads,
    categories). We sort using each message's ``internalDate`` from the API.
    """
    credentials = credentials_from_session(credentials_dict)
    service = build("gmail", "v1", credentials=credentials)

    # Use a large pool so emails from the past week don't get cut off
    pool_size = min(500, max(200, max_results * 4))
    results = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=pool_size,
            labelIds=["INBOX"],
            includeSpamTrash=False,
        )
        .execute()
    )

    refs = results.get("messages", [])
    if not refs:
        return []

    scored: list[tuple[int, str]] = []
    for ref in refs:
        mid = ref["id"]
        meta = (
            service.users()
            .messages()
            .get(userId="me", id=mid, format="metadata")
            .execute()
        )
        ts = int(meta.get("internalDate") or 0)
        scored.append((ts, mid))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_ids = [mid for _, mid in scored[:max_results]]

    emails: list[dict] = []
    for msg_id in top_ids:
        message = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        emails.append(_parse_message_to_email(message, msg_id))

    return emails
