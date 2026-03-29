import base64
from typing import Any

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

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


def get_recent_emails(credentials_dict: dict, max_results: int = 20) -> list[dict]:
    credentials = credentials_from_session(credentials_dict)
    service = build("gmail", "v1", credentials=credentials)

    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results, labelIds=["INBOX"])
        .execute()
    )

    messages = results.get("messages", [])
    emails: list[dict] = []

    for msg_ref in messages:
        msg_id = msg_ref["id"]
        message = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

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

        emails.append(
            {
                "id": msg_id,
                "subject": subject,
                "from": from_email,
                "date": date,
                "body": body[:500],
            }
        )

    return emails
