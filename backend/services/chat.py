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
_DRIVE_WORDS = re.compile(
    r"\b(drive|google drive|document|documents|doc|docs|pdf|file|files|"
    r"resume|cv|literature review|lit review|slides|sheet|sheets)\b",
    re.IGNORECASE,
)
_DRIVE_LIST_QUERY = re.compile(
    r"\b(last|recent|latest)\s+(\d{1,3})?\s*(files?|documents?|docs?)\b",
    re.IGNORECASE,
)

_DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Common words that look like keywords but aren't useful to search
_KEYWORD_STOPWORDS = {
    "ABOUT", "THAT", "WITH", "FROM", "HAVE", "THEY", "BEEN", "THIS",
    "WHAT", "TELL", "PLEASE", "JUST", "ALSO", "WHEN", "BACK", "KNOW",
    "DOES", "SOME", "STILL", "WANT", "NEED", "WILL", "MORE", "THEN",
}


def _extract_keywords(text: str) -> list[str]:
    """Extract distinctive tokens worth doing a keyword scan for:
    - Course codes like 'ITSC 2175' or 'CS101'
    - Abbreviations/acronyms like 'UIUC', 'usc', 'GRE' (2-6 letters, all same case)
    - Long words (7+ chars) that are specific nouns
    """
    keywords: list[str] = []
    # Course codes: letters + optional space + digits (e.g. "ITSC 2175", "cs101")
    for m in re.finditer(r"\b([A-Za-z]{2,6})\s*(\d{3,4})\b", text):
        keywords.append(m.group(0).replace(" ", ""))  # "ITSC2175"
        keywords.append(m.group(0))                   # "ITSC 2175"
        keywords.append(m.group(1))                   # "ITSC"
    # Abbreviations: all-caps words (UIUC, USC) OR short lowercase words that
    # are clearly acronyms typed in lowercase (uiuc, mit) — require 3+ chars
    # and exclude anything that looks like a common English word
    _common = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "had", "her", "was", "one", "our", "out", "day", "get", "has",
        "him", "his", "how", "its", "may", "new", "now", "old", "see",
        "two", "who", "did", "let", "put", "say", "she", "too", "use",
        "yet", "any", "did", "far", "few", "got", "him", "own", "why",
        "ago", "aim", "ask", "big", "bit", "due", "end", "end", "era",
        "etc", "lot", "low", "met", "off", "per", "set", "six", "ten",
        "top", "try", "via", "yes", "way", "him", "did", "hear", "back",
        "just", "like", "make", "much", "some", "such", "tell", "then",
        "they", "this", "with", "also", "been", "does", "from", "have",
        "here", "into", "more", "most", "need", "over", "said", "same",
        "than", "that", "them", "well", "were", "what", "when", "will",
        "your", "about", "after", "again", "could", "every", "first",
        "going", "great", "know", "other", "their", "there", "think",
        "where", "while", "would", "being", "came", "come", "each",
        "even", "find", "give", "good", "help", "hold", "home", "just",
        "keep", "kind", "last", "left", "life", "like", "long", "look",
        "made", "main", "mean", "mine", "must", "my", "name", "next",
        "only", "open", "part", "past", "plan", "play", "real", "right",
        "sent", "show", "side", "size", "soon", "stay", "sure", "take",
        "talk", "time", "told", "took", "true", "turn", "type", "upon",
        "used", "very", "view", "want", "ways", "week", "went", "word",
        "work", "year", "able", "both", "call", "case", "copy", "date",
        "done", "down", "drop", "else", "feel", "felt", "free", "full",
        "goes", "gone", "grow", "half", "hard", "head", "high", "idea",
        "join", "late", "lead", "less", "lets", "lost", "love", "many",
        "mark", "miss", "move", "note", "once", "page", "paid", "pick",
        "plus", "post", "pull", "push", "puts", "read", "rely", "rest",
        "role", "room", "runs", "save", "self", "send", "sign", "skip",
        "sort", "spot", "stop", "such", "task", "test", "text", "thus",
        "till", "told", "tool", "into", "you", "me", "if", "my", "or",
        "how", "any", "did",
    }
    for m in re.finditer(r"\b([A-Za-z]{3,6})\b", text):
        word = m.group(1)
        if word.lower() not in _common and word.upper() not in _KEYWORD_STOPWORDS and (
            word.isupper() or (word.islower() and len(word) >= 3 and word not in _common)
        ):
            keywords.append(word)
    # Long specific words (university/company names, etc.)
    for m in re.finditer(r"\b([A-Za-z]{7,})\b", text):
        keywords.append(m.group(1))
    return list(dict.fromkeys(keywords))  # deduplicate preserving order


def _intent(text: str) -> str:
    has_cal = bool(_CALENDAR_WORDS.search(text))
    has_email = bool(_EMAIL_WORDS.search(text))
    has_drive = bool(_DRIVE_WORDS.search(text))
    if has_cal and not has_email and not has_drive:
        return "calendar"
    if has_email and not has_cal and not has_drive:
        return "email"
    if has_drive and not has_cal and not has_email:
        return "drive"
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


def _parse_drive_list_limit(text: str, default_limit: int = 30) -> int | None:
    """Return requested drive-list limit for queries like 'last 30 files'."""
    if "drive" not in text.lower() and "file" not in text.lower() and "doc" not in text.lower():
        return None
    m = _DRIVE_LIST_QUERY.search(text)
    if not m:
        return None
    raw = m.group(2)
    if not raw:
        return default_limit
    try:
        n = int(raw)
    except ValueError:
        return default_limit
    return max(1, min(n, 100))


# ── main entry point ──────────────────────────────────────────────────────────

def create_twin_response(user_message: str, vector_store) -> str:
    drive_list_limit = _parse_drive_list_limit(user_message)
    if drive_list_limit is not None:
        files = vector_store.get_recent_drive_files(limit=drive_list_limit)
        if not files:
            return (
                "I do not have synced Drive files yet. "
                "Click Sync again and ask once it completes."
            )
        lines: list[str] = []
        for i, f in enumerate(files, start=1):
            name = f.get("name") or "Untitled"
            created = f.get("created") or f.get("modified") or "Unknown time"
            link = f.get("link") or ""
            if link:
                lines.append(f"{i}. {name} ({created}) - {link}")
            else:
                lines.append(f"{i}. {name} ({created})")
        return "Here are your most recent synced Drive files:\n" + "\n".join(lines)

    intent = _intent(user_message)
    cal_docs: list[str] = []
    email_docs: list[str] = []
    drive_docs: list[str] = []

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
        date_window = _resolve_date_window(user_message)
        if date_window and date_window[0] == date_window[1]:
            # Email query for a specific day ("today", "yesterday", weekday, etc.)
            email_docs = vector_store.get_emails_on_date(date_window[0])
            if not email_docs:
                label = date_window[0].strftime("%A, %B %d, %Y").replace(" 0", " ")
                email_docs = [f"[No emails found for {label}]"]
        else:
            # General email query (no specific date): use vector + keyword search
            context_data = vector_store.query(user_message, n_results=10)
            email_docs = _docs(context_data.get("emails") or {}, 8)

            # Keyword fallback: course codes and proper nouns that vector search misses
            keywords = _extract_keywords(user_message)
            if keywords:
                kw_docs = vector_store.search_emails_by_keywords(keywords)
                # Merge without duplicates (keyword hits first so they're in context)
                seen = set(email_docs)
                for d in kw_docs:
                    if d not in seen:
                        email_docs.append(d)
                        seen.add(d)
            email_docs = email_docs[:10]  # cap total

    if intent in ("drive", "both"):
        context_data = vector_store.query(user_message, n_results=10)
        drive_docs = _docs(context_data.get("drive") or {}, 8)

    if not cal_docs and not email_docs and not drive_docs:
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
        "Do NOT claim missing Drive access if DRIVE FILES data is present below.\n"
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

    if drive_docs:
        system += "DRIVE FILES (from Google Drive):\n"
        for doc in drive_docs:
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
