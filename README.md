# AI Chief of Staff — Personal Agent Platform

A modular, production-ready **multi-agent AI platform** that acts as a personal
Chief of Staff: it tracks GitHub work, monitors project delivery, auto-generates
reports, optimizes LinkedIn/resume/portfolio, plans learning, and keeps a
long-term AI memory — all behind a single enterprise dashboard.

> **What it is not:** a chatbot. Ten autonomous agents (each a LangGraph state
> graph) run on schedules, persist decisions to memory, and surface everything
> through charts and natural-language commands.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19 · TypeScript · Vite · Tailwind CSS v4 · shadcn-style UI · React Query · Framer Motion · Recharts |
| Backend | Django 6 · Django REST Framework · Celery · Redis |
| AI | LangGraph orchestration · provider-agnostic LLM layer (mock / Ollama / OpenAI / Gemini) |
| Data | PostgreSQL 17 · pgvector (semantic memory) |
| Auth | JWT · GitHub OAuth · Google OAuth (optional) · role-based access |
| DevOps | Docker Compose · GitHub Actions · Render |

## The 10 agents

| Agent | What it does |
|---|---|
| **GitHub** | Repos, commits, PRs, issues, releases; productivity score; repo health; inactive-repo detection; weekly analytics |
| **Daily Productivity** | Morning briefing (priorities, deadlines, workload, risk, schedule) + end-of-day wrap-up |
| **Project Performance** | Completion %, burndown, velocity, delivery prediction, risk score (HexaStack) |
| **Report** | Daily/weekly/monthly/quarterly/yearly reports; Markdown, HTML, PDF, Excel, Word export |
| **LinkedIn** | Profile scoring, recruiter-visibility analysis, post ideas, hashtags, best time to post |
| **Resume** | Auto-update from activity, ATS scoring, keyword suggestions, PDF/DOCX, versioning |
| **Portfolio** | Auto-sync from repos; a new GitHub release refreshes the matching project |
| **Learning** | Trend-aware daily suggestions + a personalized roadmap |
| **Analytics** | Cross-module aggregations (coding, time, business, learning, LinkedIn, resume) |
| **Notifications** | Rule sweep → in-app alerts for deadlines, inactive repos, low productivity, delays |

## Quick start

```bash
# 1. Backing services (Postgres + pgvector, Redis)
docker compose -f infra/docker-compose.yml up -d

# 2. Backend
cd backend
python -m venv .venv
.venv/Scripts/activate            # Windows; `source .venv/bin/activate` on Unix
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # realistic 6-week dataset, demo / demo12345
python manage.py run_agents --all # run every agent once
python manage.py runserver 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173  (proxies /api → :8000)
```

Full instructions: [docs/SETUP.md](docs/SETUP.md) · Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · API: [docs/API.md](docs/API.md) · Deploy: [docs/DEPLOY.md](docs/DEPLOY.md)

## Try the AI Assistant

Open **AI Assistant** in the sidebar and ask, in plain English:

- "Generate today's report"
- "How many commits did I make this week?"
- "Which repository needs attention?"
- "Predict delivery date for my projects"
- "Generate a LinkedIn post"
- "Update my resume"

The command router matches the intent and runs the right agent or query.

## Development

- Backend tests: `cd backend && .venv/Scripts/python -m pytest`
- Frontend tests: `cd frontend && npm run test`
- Lint/typecheck: `npm run lint` (frontend), `ruff` (backend)
- Run a single agent on demand: `python manage.py run_agents github`

## Environment

Copy `.env.example` → `.env` and adjust. Key switches:

- `AI_PROVIDER=mock` (default, offline) · `ollama` · `openai` · `gemini`
- `ALLOW_OAUTH=False` until you add `GITHUB_CLIENT_ID/SECRET` (and Google equivalents)
- `CELERY_TASK_ALWAYS_EAGER=True` runs Celery tasks inline for development without a worker

## License

This project is licensed under the SURAG-1.0 License - see the [SURAG-LICENSE](SURAG-LICENSE) file for details.
