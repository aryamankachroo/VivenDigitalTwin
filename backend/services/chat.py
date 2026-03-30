import re

from openai import OpenAI

import config

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        key = (config.OPENAI_API_KEY or "").strip()
        if not key:
            raise ValueError("OPENAI_API_KEY is not set")
        _client = OpenAI(api_key=key)
    return _client


def _wants_numbered_recent_inbox(text: str) -> bool:
    """Follow-ups like 'the email before that' need several newest messages, not RAG."""
    t = text.lower()
    if re.search(r"\bbefore\b.{0,35}\b(that|this|it)\b", t):
        return True
    if re.search(r"\b(that|this|it)\b.{0,25}\bbefore\b", t):
        return True
    if re.search(r"\b(previous|prior)\b.{0,25}\b(e-?mail|message)\b", t):
        return True
    if re.search(r"\b(e-?mail|message)\b.{0,30}\bbefore\b", t):
        return True
    if re.search(r"\bsecond\b.{0,30}\b(e-?mail|message|last|one)\b", t):
        return True
    if re.search(r"\b2nd\b", t) and re.search(r"\b(e-?mail|message)\b", t):
        return True
    if re.search(r"\bearlier\b.{0,20}\b(e-?mail|message|one)\b", t):
        return True
    if re.search(r"\bone before\b", t):
        return True
    return False


def _wants_latest_inbox_email(text: str) -> bool:
    """Single 'last / latest email' question."""
    t = text.lower()
    if not re.search(r"\b(e-?mails?|messages?)\b", t):
        return False
    return bool(
        re.search(
            r"\b(last|latest|most recent|newest|just got|receive|received)\b",
            t,
        )
    )


_RECENT_COUNT_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
}


def _explicit_recent_email_count(text: str) -> int | None:
    """Parse 'last two emails', 'last 5 messages', etc. (avoids fetching only 1)."""
    t = text.lower()
    if not re.search(r"\b(e-?mails?|messages?)\b", t):
        return None
    m = re.search(
        r"\blast\s+(one|two|three|four|five|six|seven|eight|nine|ten|"
        r"1|2|3|4|5|6|7|8|9|10)\s+(e-?mails?|messages?)\b",
        t,
    )
    if m:
        return _RECENT_COUNT_WORDS.get(m.group(1))
    m = re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten|"
        r"1|2|3|4|5|6|7|8|9|10)\s+(most recent|latest)\s+(e-?mails?|messages?)\b",
        t,
    )
    if m:
        return _RECENT_COUNT_WORDS.get(m.group(1))
    return None


def _live_inbox_fetch_count(user_message: str) -> int:
    if _wants_numbered_recent_inbox(user_message):
        return 12
    n = _explicit_recent_email_count(user_message)
    if n is not None:
        return min(max(1, n), 20)
    if _wants_latest_inbox_email(user_message):
        return 1
    return 0


def _authoritative_recent_inbox_block(credentials_dict: dict, n: int) -> str | None:
    from integrations.gmail import get_recent_emails

    emails = get_recent_emails(credentials_dict, max_results=max(1, n))
    if not emails:
        return None
    lines = [
        "NUMBERED_INBOX_MESSAGES (sorted by Gmail internalDate; 1=newest):",
        f"Showing the {len(emails)} newest messages in this pull.",
        "",
    ]
    for i, e in enumerate(emails, start=1):
        excerpt = (e.get("body") or "")[:320]
        lines.append(
            f"{i}. Subject: {e['subject']}\n"
            f"   From: {e['from']}\n"
            f"   Date: {e['date']}\n"
            f"   Body excerpt: {excerpt}"
        )
        lines.append("")
    return "\n".join(lines).strip()


def _docs_from_chroma_result(result: dict, limit: int = 3) -> list[str]:
    docs_batch = result.get("documents") or []
    if not docs_batch or not docs_batch[0]:
        return []
    return list(docs_batch[0])[:limit]


def generate_response(
    user_message: str,
    context_data: dict,
    *,
    extra_context_blocks: list[str] | None = None,
) -> str:
    extra_context_blocks = extra_context_blocks or []
    email_docs = _docs_from_chroma_result(context_data.get("emails") or {}, 4)
    cal_docs = _docs_from_chroma_result(context_data.get("calendar") or {}, 4)

    if not email_docs and not cal_docs and not extra_context_blocks:
        return (
            "I did not find any synced emails or calendar events that match "
            "that question. Try Sync again after new mail or events, or ask "
            "about something that appears in your recent sync."
        )

    context = (
        "You are a personal assistant with STRICT grounding rules.\n"
        "- Use ONLY the EMAIL and CALENDAR excerpts below. Treat them as the "
        "only source of truth.\n"
        "- If a NUMBERED_INBOX_MESSAGES block is present: message 1 is the "
        "newest in Gmail; 2 is the next oldest, etc. Use it for 'last email', "
        "'last N emails', 'email before that', 'second most recent', etc.\n"
        "- If only a single-message authoritative block is present, use it for "
        "'latest/last email' questions.\n"
        "- Calendar lines may be past or future; use dates/times exactly as "
        "written in the excerpts.\n"
        "- Do NOT invent meetings, emails, or times.\n"
        "- If the excerpts do not answer the question, say you do not have "
        "that in the synced data and suggest syncing or rephrasing.\n"
        "- Do not mention unrelated future meetings when the user only asked "
        "about a specific period unless those events fall in that period per "
        "the excerpts.\n\n"
    )

    if extra_context_blocks:
        context += "AUTHORITATIVE:\n"
        for block in extra_context_blocks:
            context += f"{block}\n\n"

    if email_docs:
        context += "EMAIL EXCERPTS (vector search):\n"
        for doc in email_docs:
            context += f"{doc}\n\n"

    if cal_docs:
        context += "CALENDAR EXCERPTS:\n"
        for doc in cal_docs:
            context += f"{doc}\n\n"

    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": user_message},
    ]

    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.35,
        max_tokens=350,
    )
    return response.choices[0].message.content or ""


def create_twin_response(
    user_message: str,
    vector_store,
    google_credentials: dict | None = None,
) -> str:
    extras: list[str] = []
    n_live = _live_inbox_fetch_count(user_message) if google_credentials else 0
    if google_credentials and n_live:
        block = _authoritative_recent_inbox_block(google_credentials, n_live)
        if block:
            extras.append(block)

    context_data = vector_store.query(user_message, n_results=8)
    return generate_response(
        user_message, context_data, extra_context_blocks=extras
    )
