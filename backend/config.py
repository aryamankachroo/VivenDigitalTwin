import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Prefer backend/.env, then repo-root .env (when running from project root)
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

CHROMA_PATH = BASE_DIR / "chroma_data"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY", "") or "").strip()
SECRET_KEY = (os.getenv("SECRET_KEY", "") or "").strip()
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# OAuthLib refuses token exchange over http unless this is set. Use only for local dev.
if FLASK_ENV == "development":
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]
