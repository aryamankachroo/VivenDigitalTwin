# TwinAI — Your AI-powered second brain

TwinAI is a personal digital twin that knows your schedule and inbox. Connect your Google account and ask it anything about your own life — it answers from your actual data, not guesswork.

## What it can do

- **Answer calendar questions** — "What are my meetings tomorrow?", "Do I have anything on Monday?", "What happened last week?"
- **Answer email questions** — "What is the last email I received?", "Did I hear back from UIUC?", "Any emails about ITSC 2175?"
- **Understand context** — knows your schedule, upcoming events, recent conversations, and deadlines

## How it gets your data

TwinAI connects to two Google data sources via read-only OAuth 2.0:

**Gmail**
Fetches your 100 most recent inbox messages and indexes them so you can ask questions about senders, subjects, and content.

**Google Calendar**
Fetches all events within a 28-day window (14 days back, 14 days forward) and indexes them so you can ask about your schedule by day, week, or event name.

All data stays local — nothing is stored on any external server. The index lives in `backend/chroma_data/` on your own machine.
