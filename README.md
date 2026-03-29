# Digital Twin MVP - Gmail + Calendar + RAG

A personal digital twin that answers questions using your real Gmail and Google Calendar data via OAuth 2.0 and retrieval-augmented generation (RAG).

## Stack

- Frontend: React + Vite + TailwindCSS + Axios
- Backend: Flask + Google APIs + ChromaDB + OpenAI
- Auth: Google OAuth 2.0 (read-only Gmail + Calendar scopes)
- Data: Chroma persistent vector store (`backend/chroma_data`)

## Prerequisites

- Python 3.9+
- Node.js 18+
- Google Cloud project
- OpenAI API key

## 1) Google Cloud setup

1. Create a Google Cloud project.
2. Enable APIs:
   - Gmail API
   - Google Calendar API
3. Configure OAuth consent screen:
   - External app (testing is fine)
   - Add your Google account under test users
4. Create OAuth Client ID:
   - Application type: Web application
   - Authorized redirect URI: `http://localhost:5000/auth/google/callback`
5. Download OAuth client credentials JSON and save it as:
   - `backend/credentials.json`

## 2) Environment setup

Copy `.env.example` to `.env` and set values:

```bash
OPENAI_API_KEY=your_openai_key_here
SECRET_KEY=your_flask_secret_key_here
FLASK_ENV=development
```

Optional env vars:

- `FRONTEND_ORIGIN=http://localhost:5173`
- `GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback`

## 3) Backend setup

```bash
cd backend
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`.

## 4) Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## 5) Usage

1. Open `http://localhost:5173`
2. Click **Connect Google Account**
3. Approve Gmail/Calendar read-only access
4. App syncs recent emails and upcoming events
5. Ask questions in chat (for example: "What meetings do I have this week?")

## API endpoints

- `GET /api/health` - health check
- `GET /api/auth/status` - whether current session is authenticated
- `GET /auth/google/login` - get Google OAuth URL
- `GET /auth/google/callback` - OAuth callback
- `POST /api/sync` - ingest Gmail + Calendar into Chroma
- `POST /api/chat` - ask digital twin questions

## Troubleshooting

- `redirect_uri_mismatch`
  - Confirm Google Cloud OAuth redirect URI exactly matches:
    `http://localhost:5000/auth/google/callback`
- `Not authenticated` from `/api/chat` or `/api/sync`
  - Re-run Google login in same browser session
- CORS / cookie issues
  - Ensure frontend uses `http://localhost:5173`
  - Ensure backend uses `CORS(... supports_credentials=True ...)`
- Missing `credentials.json`
  - Place downloaded OAuth client JSON at `backend/credentials.json`
- Empty or weak answers
  - Run sync again and ask queries likely present in recent emails/events

## Notes for MVP scope

- OAuth credentials are kept in Flask session for local MVP simplicity.
- Redis and SQLite token persistence are intentionally deferred.
- Chroma is persisted to `backend/chroma_data` for restart-safe retrieval.
