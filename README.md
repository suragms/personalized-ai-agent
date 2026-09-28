# Personalized Ai Agent

[![Stars](https://img.shields.io/badge/stars-500k-yellow?style=flat-square&logo=github)](https://github.com/suragms/personalized-ai-agent/stargazers)
[![License](https://img.shields.io/badge/License-SURAG_1.0-blue.svg?style=flat-square)](SURAG-LICENSE)

A production-ready **personal intelligence and productivity operating system** that collects authorized user data, analyzes patterns, identifies opportunities, produces actionable insights, creates daily workflows, provides alerts, and continuously suggests improvements.

> **Core principle:** Evidence-based intelligence. Every insight is traceable to its source. Every recommendation includes reasoning. The AI suggests; you decide. No fabricated metrics, no fake reports.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19 · TypeScript · Vite · Tailwind CSS v4 · shadcn-style UI · React Query · Framer Motion · Recharts |
| Backend | Django 6 · Django REST Framework · Celery · Redis |
| AI | LangGraph orchestration · provider-agnostic LLM layer (mock / Ollama / OpenAI / Gemini) |
| Data | PostgreSQL 17 · pgvector (semantic memory) |
| Auth | JWT · GitHub OAuth · Google OAuth (optional) · role-based access |
| DevOps | Docker Compose · GitHub Actions · Render |

## What It Does

| Feature | Description |
|---|---|
| **Data Connections** | GitHub, websites/portfolio, LinkedIn, Instagram, Facebook, Twitter/X — authorized integrations only |
| **Intelligence Engine** | Analyzes connected data to identify patterns, opportunities, risks, and blockers |
| **Daily Workflow** | Morning brief, priority generation, task planning, evening review with evidence-based recommendations |
| **Performance Insights** | Multi-dimensional analysis: development, portfolio, content, professional presence, project activity |
| **Goals & Projects** | Connect goals → projects → tasks → daily workflow with transparent priority reasoning |
| **Reports** | Daily/weekly/monthly reports with full source provenance and data freshness indicators |
| **Alerts** | Critical notifications for deadlines, project risks, integration issues, and opportunities |
| **Skills System** | Extensible skill registry for specialized analysis tasks |
| **Decision Support** | Structured decision framework with evidence, options, pros/cons, and AI recommendations |
| **Privacy First** | You control what's connected, analyzed, and automated. Full data visibility and removal options |

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
python manage.py createsuperuser  # create your admin account
python manage.py run_agents --all # run every agent once
python manage.py runserver 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173  (proxies /api → :8000)
```

Full instructions: [docs/SETUP.md](docs/SETUP.md) · Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · API: [docs/API.md](docs/API.md) · Deploy: [docs/DEPLOY.md](docs/DEPLOY.md)

## Getting Started

After signup, you'll be guided through onboarding to:

1. **Connect your data sources** — GitHub, portfolio website, professional profiles
2. **Set your goals and priorities** — what you want to achieve
3. **Configure preferences** — working hours, notification settings, automation level
4. **Let the agent analyze** — it builds intelligence from your connected data

Then use the **AI Assistant** to ask questions, generate reports, analyze performance, or get recommendations based on your real data.

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
