from datetime import date

import chromadb
from chromadb.utils import embedding_functions

import config


def _extract_date_str(start: str) -> str:
    """Extract YYYY-MM-DD from a datetime or date string."""
    if not start:
        return ""
    return start[:10]  # "2026-03-30T10:00:00-05:00" -> "2026-03-30"


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

    def collection_counts(self) -> dict[str, int]:
        return {
            "emails": self.emails_collection.count(),
            "calendar": self.calendar_collection.count(),
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
        return {"emails": email_results, "calendar": calendar_results}
