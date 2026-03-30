# Echo — My AI-powered second brain

This is a personal digital twin that knows my schedule, inbox and drive. Connect your Google account and ask it anything about your own life — it answers from your actual data, not guesswork.

## What it can do

- **Answer calendar questions** — "What are my meetings tomorrow?", "Do I have anything on Monday?", "What happened last week?"
- **Answer email questions** — "What is the last email I received?", "Did I hear back from UIUC?", "Any emails about ITSC 2175?"
- **Answer Drive questions** — "What are my last 30 files in Drive?", "Do I have a resume file?", "Show recent docs and links"
- **Understand context** — knows your schedule, upcoming events, recent conversations, and deadlines

## How it gets your data

Echo connects to three Google data sources via read-only OAuth 2.0:

**Gmail**
Fetches your 100 most recent inbox messages and indexes them so you can ask questions about senders, subjects, and content.

**Google Calendar**
Fetches all events within a 28-day window (14 days back, 14 days forward) and indexes them so you can ask about your schedule by day, week, or event name.

**Google Drive**
Fetches your 30 most recently created non-trashed files and indexes metadata (name, type, owner, created/modified time, and link) so you can ask for recent files and file lookup questions.

All data stays local — nothing is stored on any external server. The index lives in `backend/chroma_data/` on your own machine.
