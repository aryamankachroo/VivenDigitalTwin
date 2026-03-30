from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from auth import credentials_from_session


def _format_event(event: dict) -> dict:
    start = event["start"].get("dateTime", event["start"].get("date"))
    end = event["end"].get("dateTime", event["end"].get("date"))
    attendees = [a.get("email") for a in event.get("attendees", []) if a.get("email")]
    return {
        "id": event.get("id", ""),
        "summary": event.get("summary", "No Title"),
        "start": start,
        "end": end,
        "description": event.get("description", "") or "",
        "attendees": attendees,
    }


def get_calendar_events_for_sync(
    credentials_dict: dict,
    days_back: int = 14,
    days_forward: int = 14,
) -> list[dict]:
    """All events from days_back ago through days_forward from now, paginated."""
    credentials = credentials_from_session(credentials_dict)
    service = build("calendar", "v3", credentials=credentials)

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=days_back)).isoformat().replace("+00:00", "Z")
    time_max = (now + timedelta(days=days_forward)).isoformat().replace("+00:00", "Z")

    out: list[dict] = []
    page_token: str | None = None

    while True:
        kwargs: dict = {
            "calendarId": "primary",
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 250,
        }
        if page_token:
            kwargs["pageToken"] = page_token

        result = service.events().list(**kwargs).execute()
        for item in result.get("items", []):
            out.append(_format_event(item))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return out
