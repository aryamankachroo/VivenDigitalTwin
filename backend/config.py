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
    # Use the frontend origin so OAuth callback sets cookie for the same origin
    # (Vite dev server proxies /auth -> backend).
    "GOOGLE_REDIRECT_URI",
    "http://localhost:5173/auth/google/callback",
)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# How many newest inbox messages to embed per sync (pool for sorting is capped in gmail.py).
SYNC_EMAIL_LIMIT = int(os.getenv("SYNC_EMAIL_LIMIT", "100"))
# How many newest Drive files (by created time) to embed per sync.
SYNC_DRIVE_LIMIT = int(os.getenv("SYNC_DRIVE_LIMIT", "30"))
