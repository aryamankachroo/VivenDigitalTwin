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


def _list_events(
    credentials_dict: dict,
    time_min: str,
    time_max: str | None,
    max_results: int,
) -> list[dict]:
    credentials = credentials_from_session(credentials_dict)
    service = build("calendar", "v3", credentials=credentials)

    kwargs: dict = {
        "calendarId": "primary",
        "timeMin": time_min,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_max is not None:
        kwargs["timeMax"] = time_max

    events_result = service.events().list(**kwargs).execute()
    items = events_result.get("items", [])
    return [_format_event(e) for e in items]


def get_upcoming_events(credentials_dict: dict, max_results: int = 20) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return _list_events(
        credentials_dict, time_min=now, time_max=None, max_results=max_results
    )


def get_past_events(
    credentials_dict: dict, days_back: int = 21, max_results: int = 100
) -> list[dict]:
    """Events that already started (through now), for RAG queries like 'last week'."""
    now = datetime.now(timezone.utc)
    time_max = now.isoformat().replace("+00:00", "Z")
    time_min = (now - timedelta(days=days_back)).isoformat().replace("+00:00", "Z")
    return _list_events(
        credentials_dict, time_min=time_min, time_max=time_max, max_results=max_results
    )


def get_calendar_events_for_sync(credentials_dict: dict) -> list[dict]:
    """Past window + upcoming, deduped by event id for the vector store."""
    past = get_past_events(credentials_dict)
    upcoming = get_upcoming_events(credentials_dict)
    by_id: dict[str, dict] = {}
    for e in past + upcoming:
        eid = e.get("id") or ""
        key = eid if eid else f"__noid_{len(by_id)}"
        by_id[key] = e
    return list(by_id.values())
