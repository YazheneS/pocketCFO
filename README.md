# PocketCFO

PocketCFO is a voice-first transaction UI backed by FastAPI, Supabase, and Groq.

## Official runtime

```text
voice-module (port 5000)
    |
    +--> FastAPI backend (port 8000)
            |
            +--> Supabase transactions table
            +--> Groq chatbot through POST /chat
```

The official backend package is `backend.app`. The archived folders under `archive/` are not part of the runtime.

## Requirements

Install the dependencies from the project root:

```powershell
pip install -r requirements.txt
```

Set `SUPABASE_URL`, `SUPABASE_KEY`, and `GROQ_API_KEY` in `.env`. Authentication is disabled: the login screen accepts any email/password, and the backend uses a single shared demo user. Run `database/migrations/003_disable_auth.sql` once in the Supabase SQL editor.

The existing Supabase project remains the database. The canonical schema reference is [database/schema.sql](database/schema.sql). No local database is created. For an existing project, run `database/migrations/003_disable_auth.sql` and then `database/migrations/004_unify_transaction_storage.sql` in the Supabase SQL editor; the latter moves existing voice-module records into the shared transaction account.

## Run locally

From the project root, start the backend:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

In a second terminal, start the current frontend and voice API:

```powershell
cd voice-module
python server.py
```

Open <http://127.0.0.1:5000>.

## API

- `GET /health`
- `GET /transactions`
- `GET /transactions/{transaction_id}`
- `POST /transactions`
- `PUT /transactions/{transaction_id}`
- `DELETE /transactions/{transaction_id}`
- `GET /transactions/export/csv`
- `GET /transactions/export/pdf`
- `POST /chat`

## Docker Compose

The Compose stack contains the official FastAPI backend and voice module. It uses the existing Supabase project and does not create a database.

```powershell
docker compose up --build
```
