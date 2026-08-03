# Architecture

## Overview

The platform is a modular monorepo: a Django REST API with ten agent apps, a
provider-agnostic AI layer, a pgvector memory store, and a React dashboard.

```
┌────────────────────────────┐        ┌──────────────────────────────────────┐
│   React 19 + Vite (5173)   │  /api  │        Django REST API (8000)        │
│   Dashboard · AI Assistant │ ─────► │  accounts · github · productivity ·  │
└────────────────────────────┘        │  projects · reports · linkedin ·     │
                                      │  resume · portfolio · learning ·     │
                                      │  analytics · notifications           │
                                      │            │  │                     │
                                      │  ai (LLM)  │  memory (pgvector)      │
                                      └────────────┼──┼─────────────────────┘
                                                   │  │
                                          ┌────────┴──┴────────┐
                                          │  Celery + Redis    │
                                          │  beat schedules    │
                                          └────────────────────┘
```

## Clean architecture per agent

Every agent app follows the same pattern so the platform is uniform and easy to
deepen:

```
apps/<agent>/
├── models.py      # Django ORM models (time-series, indexed)
├── services.py    # pure computation: scoring, aggregation, prediction
├── agents.py      # LangGraph StateGraph: collect → analyze → generate → persist
├── tasks.py       # Celery entrypoints (schedules call these)
├── serializers.py # DRF serializers
├── views.py       # ViewSets + action endpoints
├── urls.py        # routed under /api/<agent>/
└── migrations/
```

The **services layer is deterministic and data-driven** — the source of truth
for every number on the dashboard. The **AI layer enhances prose** (insights,
briefings, reports) and is never the only path between users and their data:
every `generate_prose()` call falls back to a template built from real metrics.

## AI layer (`apps/ai`)

- `providers/` — `LLMProvider` ABC with four backends:
  - **mock** (default): deterministic, offline. Preserves formatted markdown;
    digests raw data; returns hash-based embeddings.
  - **ollama** (localhost:11434), **openai**, **gemini** — real generation,
    selected via `AI_PROVIDER`.
- `graphs/base.py` — `AgentGraph`: wraps LangGraph's `StateGraph` when installed
  and transparently falls back to a sequential executor otherwise. Nodes return
  **partial updates**, merged into the shared state (so `owner` threads through).
- `command_router.py` — maps natural-language commands to agent capabilities via
  keyword intents (+ optional LLM classification for real providers).

## Memory (`apps/memory`)

- `MemoryEntry` stores facts/decisions/preferences with a **pgvector embedding**
  (`vector(384)`), enabling cosine similarity search.
- `ConversationLog` records assistant interactions; `UserPreference` persists
  choices. Agents call `remember_decision()` to record what they did, so future
  runs "remember previous decisions."

## Scheduling

Celery beat (see `config/celery.py`) drives the platform when a worker runs:

| Schedule | Task |
|---|---|
| hourly | GitHub analytics refresh · notification sweep |
| 24h | morning briefing, EOD wrap-up, daily report |
| 7d | weekly report |

On-demand (no worker needed): `python manage.py run_agents --all` runs every
agent synchronously. Set `CELERY_TASK_ALWAYS_EAGER=True` for inline execution.

## Security

- JWT access/refresh via `simplejwt`; roles `owner`/`admin`/`viewer` enforced by
  `core.permissions`.
- OAuth (GitHub/Google) is a manual code-exchange flow, gated by
  `ALLOW_OAUTH` + client secrets in the environment (never the client).
- Secrets live in the backend environment only; the frontend never sees keys.

## Data flow example — "Generate today's report"

1. Frontend posts `{command}` → `POST /api/ai/command/`.
2. `command_router` matches intent `generate_report`.
3. The report service aggregates GitHub, tasks, and project data for the period.
4. `generate_prose()` asks the configured LLM; the mock provider passes the
   templated markdown through; a real provider writes it.
5. The `Report` row is persisted (Markdown + HTML) and returned to the dashboard,
   where it can be exported as PDF / Excel / Word.
