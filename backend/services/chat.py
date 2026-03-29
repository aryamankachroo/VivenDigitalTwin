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


def _docs_from_chroma_result(result: dict, limit: int = 3) -> list[str]:
    docs_batch = result.get("documents") or []
    if not docs_batch or not docs_batch[0]:
        return []
    return list(docs_batch[0])[:limit]


def generate_response(user_message: str, context_data: dict) -> str:
    context = (
        "You are a helpful personal digital twin. Answer using the user's "
        "email and calendar context below. Calendar snippets may include "
        "recent past events and upcoming events from the last sync. If the "
        "answer is not in the context, say you do not have that information "
        "from their synced data.\n\n"
    )

    email_docs = _docs_from_chroma_result(context_data.get("emails") or {}, 3)
    if email_docs:
        context += "RECENT EMAILS:\n"
        for doc in email_docs:
            context += f"{doc}\n\n"

    cal_docs = _docs_from_chroma_result(context_data.get("calendar") or {}, 3)
    if cal_docs:
        context += "UPCOMING EVENTS:\n"
        for doc in cal_docs:
            context += f"{doc}\n\n"

    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": user_message},
    ]

    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=350,
    )
    return response.choices[0].message.content or ""


def create_twin_response(user_message: str, vector_store) -> str:
    context_data = vector_store.query(user_message)
    return generate_response(user_message, context_data)
