import re
from datetime import date, timedelta

from openai import OpenAI

import config

_client: OpenAI | None = None

# ── intent detection ──────────────────────────────────────────────────────────

_CALENDAR_WORDS = re.compile(
    r"\b(meeting|meetings|event|events|schedule|calendar|class|classes|"
    r"appointment|appointments|lecture|lectures|seminar|session|sessions|"
    r"what do i have|what's on|whats on|am i free|am i busy|do i have)\b",
    re.IGNORECASE,
)
_EMAIL_WORDS = re.compile(
    r"\b(email|emails|inbox|message|messages|mail|sender|subject|received|"
    r"last email|recent email|unread)\b",
    re.IGNORECASE,
)

_DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _intent(text: str) -> str:
    has_cal = bool(_CALENDAR_WORDS.search(text))
    has_email = bool(_EMAIL_WORDS.search(text))
    if has_cal and not has_email:
        return "calendar"
    if has_email and not has_cal:
        return "email"
    return "both"


# ── date window resolver ──────────────────────────────────────────────────────

def _resolve_date_window(text: str) -> tuple[date, date] | None:
    """
    Parse time references in the user's message and return (start, end) dates.
    Returns None if no specific date reference is found (fall back to vector search).
    """
    today = date.today()
    t = text.lower()

    if "tomorrow" in t:
        d = today + timedelta(days=1)
        return (d, d)

    if "yesterday" in t:
        d = today - timedelta(days=1)
        return (d, d)

    if "today" in t or "tonight" in t or "right now" in t:
        return (today, today)

    # week ranges
    week_start = today - timedelta(days=today.weekday())  # Monday of current week
    if "next week" in t:
        s = week_start + timedelta(days=7)
        return (s, s + timedelta(days=6))
    if "last week" in t:
        s = week_start - timedelta(days=7)
        return (s, s + timedelta(days=6))
    if "this week" in t:
        return (week_start, week_start + timedelta(days=6))

    # named days: "on Monday", "last Monday", "next Friday", etc.
    for i, day in enumerate(_DAY_NAMES):
        if day in t:
            delta = (i - today.weekday()) % 7
            if "last " + day in t:
                # explicitly last occurrence
                delta = delta - 7 if delta != 0 else -7
                d = today + timedelta(days=delta)
            elif "next " + day in t or delta == 0:
                # next occurrence (or same weekday = next week)
                delta = delta if delta != 0 else 7
                d = today + timedelta(days=delta)
            else:
                # bare day name: nearest upcoming
                d = today + timedelta(days=delta)
            return (d, d)

    return None  # no date reference found


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        key = (config.OPENAI_API_KEY or "").strip()
        if not key:
            raise ValueError("OPENAI_API_KEY is not set")
        _client = OpenAI(api_key=key)
    return _client


def _docs(result: dict, limit: int = 8) -> list[str]:
    docs_batch = result.get("documents") or []
    if not docs_batch or not docs_batch[0]:
        return []
    return list(docs_batch[0])[:limit]


# ── main entry point ──────────────────────────────────────────────────────────

def create_twin_response(user_message: str, vector_store) -> str:
    intent = _intent(user_message)
    cal_docs: list[str] = []
    email_docs: list[str] = []

    if intent in ("calendar", "both"):
        date_window = _resolve_date_window(user_message)
        if date_window:
            # Date-based query: skip vector search, filter directly by date
            cal_docs = vector_store.get_events_in_range(*date_window)
            date_label = (
                date_window[0].strftime("%A, %B %d").replace(" 0", " ")
                if date_window[0] == date_window[1]
                else f"{date_window[0]} \u2013 {date_window[1]}"
            )
            if not cal_docs:
                cal_note = f"[No calendar events found for {date_label}]"
                cal_docs = [cal_note]
        else:
            # General calendar query (no date): use vector search
            context_data = vector_store.query(user_message, n_results=10)
            cal_docs = _docs(context_data.get("calendar") or {}, 8)

    if intent in ("email", "both"):
        context_data = vector_store.query(user_message, n_results=10)
        email_docs = _docs(context_data.get("emails") or {}, 8)

    if not cal_docs and not email_docs:
        return (
            "I do not have that in the synced data. "
            "Try clicking Sync again to refresh, then ask again."
        )

    today_str = date.today().strftime("%A, %B %d, %Y").replace(" 0", " ")
    system = (
        f"You are a personal digital twin. Today is {today_str}.\n"
        "Answer the user's question using ONLY the data sections below.\n"
        "Do NOT let email content override or cancel calendar events.\n"
        "Do NOT let calendar data override email content.\n"
        "Each section is a separate, authoritative source. "
        "If the answer is not in the data, say so.\n\n"
    )

    if cal_docs:
        system += "CALENDAR EVENTS (from Google Calendar):\n"
        for doc in cal_docs:
            system += f"{doc}\n\n"

    if email_docs:
        system += "EMAILS (from Gmail):\n"
        for doc in email_docs:
            system += f"{doc}\n\n"

    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=400,
    )
    return response.choices[0].message.content or ""
