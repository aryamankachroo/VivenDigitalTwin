import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, session
from flask_cors import CORS

import config
from auth import credentials_from_callback, get_auth_url
from integrations.calendar import get_calendar_events_for_sync
from integrations.gmail import get_recent_emails
from services.chat import create_twin_response
from services.embeddings import VectorStore

app = Flask(__name__)
app.secret_key = config.SECRET_KEY or secrets.token_hex(32)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

CORS(
    app,
    supports_credentials=True,
    origins=[config.FRONTEND_ORIGIN],
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"],
)

vector_store = VectorStore()


def _credentials_ok() -> bool:
    return bool(session.get("google_credentials"))


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    return jsonify(
        {
            "authenticated": _credentials_ok(),
            "last_synced_at": session.get("last_synced_at"),
        }
    )


@app.route("/auth/google/login", methods=["GET"])
def google_login():
    if not Path(config.CREDENTIALS_FILE).is_file():
        return (
            jsonify(
                {
                    "error": "Missing credentials.json in backend/. "
                    "Download OAuth client JSON from Google Cloud Console."
                }
            ),
            500,
        )
    auth_url, state, code_verifier = get_auth_url()
    session["oauth_state"] = state
    session["oauth_code_verifier"] = code_verifier
    return jsonify({"auth_url": auth_url})


@app.route("/auth/google/callback", methods=["GET"])
def google_callback():
    expected_state = session.get("oauth_state")
    returned_state = request.args.get("state")
    if (
        not expected_state
        or not returned_state
        or returned_state != expected_state
    ):
        return (
            "<html><body>Invalid OAuth state. Close this window and try again.</body></html>",
            400,
        )

    code_verifier = session.get("oauth_code_verifier")
    if not code_verifier:
        return (
            "<html><body>Missing PKCE session. Close this window and connect again from the app.</body></html>",
            400,
        )

    if request.args.get("error"):
        err = request.args.get("error")
        return f"<html><body>Authorization failed: {err}</body></html>", 400

    try:
        request_url = request.url
        if request.headers.get("X-Forwarded-Proto") == "https":
            request_url = request_url.replace("http://", "https://", 1)
        creds = credentials_from_callback(
            request_url, expected_state, code_verifier
        )
        session["google_credentials"] = creds
    except Exception as e:
        return (
            f"<html><body>Token exchange failed: {e!s}. Close and retry.</body></html>",
            400,
        )
    finally:
        session.pop("oauth_state", None)
        session.pop("oauth_code_verifier", None)

    return """
    <!DOCTYPE html>
    <html><head><title>Authorized</title></head>
    <body>
      <script>
        if (window.opener) {
          window.opener.postMessage({ type: 'auth_success' }, '*');
        }
        window.close();
      </script>
      <p>You can close this window.</p>
    </body></html>
    """


@app.route("/api/sync", methods=["POST"])
def sync_data():
    if not _credentials_ok():
        return jsonify({"error": "Not authenticated"}), 401

    credentials = session["google_credentials"]
    emails = get_recent_emails(credentials, max_results=config.SYNC_EMAIL_LIMIT)
    events = get_calendar_events_for_sync(credentials)
    vector_store.add_emails(emails)
    vector_store.add_events(events)

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    session["last_synced_at"] = now_iso

    counts = vector_store.collection_counts()

    return jsonify(
        {
            "synced_emails": len(emails),
            "synced_events": len(events),
            "last_synced_at": now_iso,
            "index_email_documents": counts["emails"],
            "index_calendar_documents": counts["calendar"],
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    if not _credentials_ok():
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not message or not str(message).strip():
        return jsonify({"error": "message is required"}), 400

    if not config.OPENAI_API_KEY:
        return jsonify({"error": "OPENAI_API_KEY is not configured"}), 500

    try:
        response_text = create_twin_response(
            str(message).strip(),
            vector_store,
            google_credentials=session.get("google_credentials"),
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"response": response_text})


if __name__ == "__main__":
    app.run(debug=config.FLASK_ENV == "development", port=5000)
