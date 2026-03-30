from datetime import date, datetime
from email.utils import parsedate_to_datetime

import chromadb
from chromadb.utils import embedding_functions

import config


def _extract_date_str(start: str) -> str:
    """Extract YYYY-MM-DD from a datetime or date string."""
    if not start:
        return ""
    return start[:10]  # "2026-03-30T10:00:00-05:00" -> "2026-03-30"


def _parse_email_header_date(header: str) -> str:
    """Parse Date header into YYYY-MM-DD in local time; fallback to empty string."""
    if not header:
        return ""
    try:
        dt: datetime = parsedate_to_datetime(header)
        # Convert to local date if timezone-aware
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt.date().isoformat()
    except Exception:
        return ""


class VectorStore:
    def __init__(self) -> None:
        config.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(config.CHROMA_PATH))
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.OPENAI_API_KEY or None,
            model_name="text-embedding-3-small",
        )
        self.emails_collection = self.client.get_or_create_collection(
            name="emails",
            embedding_function=self.openai_ef,
        )
        self.calendar_collection = self.client.get_or_create_collection(
            name="calendar",
            embedding_function=self.openai_ef,
        )
        self.drive_collection = self.client.get_or_create_collection(
            name="drive",
            embedding_function=self.openai_ef,
        )

    def add_emails(self, emails: list[dict]) -> None:
        if not emails:
            return
        documents: list[str] = []
        metadatas: list[dict] = []
        ids: list[str] = []

        for email in emails:
            doc = (
                f"Subject: {email['subject']}\nFrom: {email['from']}\n"
                f"Date: {email['date']}\n\n{email['body']}"
            )
            documents.append(doc)
            metadatas.append(
                {
                    "type": "email",
                    "subject": (email["subject"] or "")[:512],
                    "from_addr": (email["from"] or "")[:512],
                    "date": _parse_email_header_date(email.get("date", "")),
                }
            )
            ids.append(f"email_{email['id']}")

        self.emails_collection.upsert(
            documents=documents, metadatas=metadatas, ids=ids
        )

    def add_events(self, events: list[dict]) -> None:
        if not events:
            return
        documents: list[str] = []
        metadatas: list[dict] = []
        ids: list[str] = []

        for event in events:
            attendees_str = ", ".join(event.get("attendees") or [])
            doc = (
                f"Event: {event['summary']}\nStart: {event['start']}\n"
                f"End: {event['end']}\nDescription: {event['description']}\n"
                f"Attendees: {attendees_str}"
            )
            documents.append(doc)
            metadatas.append(
                {
                    "type": "event",
                    "summary": (event["summary"] or "")[:512],
                    # Store the date so we can filter without vector search
                    "date": _extract_date_str(event.get("start", "")),
                }
            )
            eid = event.get("id") or f"hash_{hash(doc)}"
            ids.append(f"event_{eid}")

        self.calendar_collection.upsert(
            documents=documents, metadatas=metadatas, ids=ids
        )

    def add_files(self, files: list[dict]) -> None:
        if not files:
            return
        documents: list[str] = []
        metadatas: list[dict] = []
        ids: list[str] = []

        for file in files:
            doc = (
                f"File: {file['name']}\nType: {file['type']}\n"
                f"Created: {file.get('created', '')}\n"
                f"Modified: {file['modified']}\nOwner: {file['owner']}\n"
                f"Link: {file.get('link', '')}"
            )
            documents.append(doc)
            metadatas.append(
                {
                    "type": "drive_file",
                    "name": (file["name"] or "")[:512],
                    "file_type": (file["type"] or "")[:512],
                    "link": (file.get("link") or "")[:512],
                    "created": (file.get("created") or "")[:64],
                    "modified": (file.get("modified") or "")[:64],
                    "owner": (file.get("owner") or "")[:512],
                }
            )
            fid = file.get("id") or f"hash_{hash(doc)}"
            ids.append(f"file_{fid}")

        self.drive_collection.upsert(
            documents=documents, metadatas=metadatas, ids=ids
        )

    def get_recent_drive_files(self, limit: int = 30) -> list[dict]:
        """Return most recent synced Drive files sorted by created/modified time."""
        all_data = self.drive_collection.get(include=["metadatas"])
        metas = all_data.get("metadatas") or []
        rows: list[dict] = []
        for meta in metas:
            m = meta or {}
            rows.append(
                {
                    "name": m.get("name", ""),
                    "type": m.get("file_type", ""),
                    "created": m.get("created", ""),
                    "modified": m.get("modified", ""),
                    "owner": m.get("owner", ""),
                    "link": m.get("link", ""),
                }
            )

        rows.sort(key=lambda r: (r.get("created") or r.get("modified") or ""), reverse=True)
        return rows[: max(1, limit)]

    def get_events_in_range(self, start: date, end: date) -> list[str]:
        """Return all calendar event documents whose start date is in [start, end].
        This is used for date-based queries like 'tomorrow' or 'Monday' where
        semantic search would fail to match ISO date strings."""
        all_data = self.calendar_collection.get(include=["documents", "metadatas"])
        docs = all_data.get("documents") or []
        metas = all_data.get("metadatas") or []

        result: list[str] = []
        for doc, meta in zip(docs, metas):
            date_str = (meta or {}).get("date", "")
            if not date_str:
                # Fallback: try to parse the date from the doc text
                for line in doc.splitlines():
                    if line.startswith("Start:"):
                        date_str = line.split(":", 1)[1].strip()[:10]
                        break
            if date_str:
                try:
                    event_date = date.fromisoformat(date_str)
                    if start <= event_date <= end:
                        result.append(doc)
                except ValueError:
                    pass

        return result

    def get_emails_on_date(self, day: date) -> list[str]:
        """Return all email documents whose Date header falls on ``day``.

        This uses the normalized ``date`` metadata populated from the Date header,
        and falls back to scanning the document text for the Date line.
        """
        all_data = self.emails_collection.get(include=["documents", "metadatas"])
        docs = all_data.get("documents") or []
        metas = all_data.get("metadatas") or []

        target = day.isoformat()
        result: list[str] = []
        for doc, meta in zip(docs, metas):
            date_str = (meta or {}).get("date", "")
            if not date_str:
                for line in doc.splitlines():
                    if line.startswith("Date:"):
                        date_str = _extract_date_str(
                            line.split(":", 1)[1].strip() or ""
                        )
                        break
            if date_str == target:
                result.append(doc)

        return result

    def search_emails_by_keywords(self, keywords: list[str]) -> list[str]:
        """Case-insensitive substring scan across all stored email documents.
        Used as a fallback when vector search misses exact codes/names."""
        if not keywords:
            return []
        all_data = self.emails_collection.get(include=["documents"])
        docs = all_data.get("documents") or []
        matched: list[str] = []
        for doc in docs:
            doc_lower = doc.lower()
            if any(kw.lower() in doc_lower for kw in keywords):
                matched.append(doc)
        return matched

    def collection_counts(self) -> dict[str, int]:
        return {
            "emails": self.emails_collection.count(),
            "calendar": self.calendar_collection.count(),
            "drive": self.drive_collection.count(),
        }

    def query(self, query_text: str, n_results: int = 5) -> dict:
        email_results = self.emails_collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        calendar_results = self.calendar_collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        drive_results = self.drive_collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
        return {
            "emails": email_results,
            "calendar": calendar_results,
            "drive": drive_results,
        }
