import chromadb
from chromadb.utils import embedding_functions

import config


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
                }
            )
            eid = event.get("id") or f"hash_{hash(doc)}"
            ids.append(f"event_{eid}")

        self.calendar_collection.upsert(
            documents=documents, metadatas=metadatas, ids=ids
        )

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
