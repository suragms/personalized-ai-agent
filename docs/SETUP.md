# Setup

## Prerequisites

- **Python 3.12+** and **Node 20+**
- **Docker** (for PostgreSQL + pgvector and Redis) — or a PostgreSQL 17 server
  with the `vector` extension installed manually
- **Git**

> Note: if a local PostgreSQL already occupies port **5432**, the compose file
> maps Postgres to host port **5433** (and `.env` already points there).

## 1. Backing services

```bash
docker compose -f infra/docker-compose.yml up -d
# containers: agent_db (pgvector/pgvector:pg17, port 5433), agent_redis (redis:7, port 6379)
```

## 2. Environment

```bash
cp .env.example .env
```

Edit `.env` — for local development the defaults work as-is (`AI_PROVIDER=mock`).

## 3. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    Unix/mac: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # or: python manage.py init_admin --password <pw>
python manage.py run_agents --all   # optional: warm every agent once
python manage.py runserver 0.0.0.0:8000
```

The API is at `http://localhost:8000/api/` (health: `/api/health/`).

## 4. Frontend

```bash
cd frontend
npm install
npm run dev       # http://localhost:5173  (Vite proxies /api → :8000)
```

Sign in with the superuser you created in step 3.

## 5. Scheduler (optional)

With a Redis backend running, start a Celery worker + beat to automate briefings,
reports, and the Intelligence Engine:

```bash
cd backend
.venv/Scripts/python -m celery -A config worker -l info --pool=solo
.venv/Scripts/python -m celery -A config beat -l info
```

Beat also runs the Phase 3 intelligence jobs (see
`CELERY_BEAT_SCHEDULE` in `config/settings.py`): `intelligence.check_freshness`
every 6 hours, `intelligence.daily_intelligence` at 05:30, and
`intelligence.evening_review` at 22:00.

For pure development you can skip this — run agents manually with
`python manage.py run_agents github reports`, or POST
`/api/intelligence/insights/generate/` to run the engine on demand.

## Switching AI providers

| Provider | `.env` |
|---|---|
| mock (default) | `AI_PROVIDER=mock` |
| Ollama | `AI_PROVIDER=ollama` + `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| OpenAI | `AI_PROVIDER=openai` + `OPENAI_API_KEY`, `OPENAI_MODEL` |
| Gemini | `AI_PROVIDER=gemini` + `GEMINI_API_KEY`, `GEMINI_MODEL` |
| Groq | `AI_PROVIDER=groq` (or `grok`) + `GROQ_API_KEY`, `GROQ_MODEL` |
| GetUniKey | `AI_PROVIDER=getunikey` + `GETUNIKEY_API_KEY` |
| OpenCode | `AI_PROVIDER=opencode` + `OPENCODE_API_KEY` |

The platform degrades gracefully: if a provider is unset/unavailable it falls
back to deterministic templated output.

## Common commands

```bash
python manage.py run_agents github productivity projects reports linkedin resume portfolio learning analytics notifications
python manage.py shell                 # interactive
cd frontend && npm run lint && npm run test && npm run build
cd backend && python -m pytest
```

## Troubleshooting

- **`password authentication failed for user "agent"`** → you're connecting to a
  local PostgreSQL on 5432. Use the Docker Postgres on 5433 (see `.env`).
- **Celery tasks hang** → ensure Redis is up (`docker compose up -d redis`) or
  set `CELERY_TASK_ALWAYS_EAGER=True`.
- **Port 8000 in use** → `python manage.py runserver 8001` and update the Vite
  proxy target in `frontend/vite.config.ts`.
