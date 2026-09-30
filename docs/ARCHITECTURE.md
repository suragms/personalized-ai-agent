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

## Intelligence Engine (`apps/intelligence`)

The Phase 3 pipeline turns authorized connected data into decisions — with every
step evidence-linked and provenance-tagged:

```
Connected data ──► DataSnapshot (content-hashed, per-source)
      │
      ▼
Deterministic analyzers (github/analyzers.py — activity, repo health,
      │                 PRs, issues, releases; NO_DATA rule: a missing
      │                 source is UNAVAILABLE_DATA, never a zero finding)
      ▼
AnalysisFinding ──► priority scoring ──► Insight upsert (owner + dedup_key)
      │                  severity base + confidence + freshness +           │
      │                  deadline + goal relevance                         │
      ▼                                                                    ▼
AI interpretation (facts-only prompt; stored ONLY when             Recommendation ──► Task
      │            provenance is REAL_AI_PROVIDER — mock never                 │  (Task.dedup_key =
      │            fakes an interpretation)                                    │   insight:<dedup_key>)
      ▼
DailyPlan (morning brief / evening review) · Alert (dedup + cooldown) · Report
```

Key guarantees:

- **Provenance** (`intelligence/provenance.py`): every insight/report/task stores
  where its data came from — `REAL_CONNECTED_DATA`, `STALE_DATA`,
  `UNAVAILABLE_DATA`, `REAL_AI_PROVIDER`, `MOCK_PROVIDER`, …
- **Freshness** (`FRESHNESS_THRESHOLDS`): per-source-type thresholds (github
  24h/72h, website/linkedin/social 7d/14d, manual 30d/90d, default 24h/72h;
  `sync_frequency_hours` wins when set) → `fresh`/`aging`/`stale`/`unavailable`.
- **Confidence**: `high`/`medium`/`low`/`insufficient` derived from evidence
  count, freshness and connectivity.
- **Idempotency**: insights upsert on `(owner, dedup_key)`; tasks dedup via
  `Task.dedup_key` with a 14-day done cooldown; alerts bump `occurrences`
  inside a 24h cooldown and never re-raise dismissed rows.
- **Expiry**: a successful scope run immediately expires engine insights that
  were not reconfirmed; analyzer failures skip that scope's expiry.
- **No fabrication**: reports return `400 insufficient_data` (and persist
  nothing) instead of writing a zero-metric report; `InsightEngine.run()` skips
  the github scope entirely when no repositories exist.

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

Celery beat (see `config/settings.py::CELERY_BEAT_SCHEDULE`; names are asserted
by `tests/test_celery_schedule.py`) drives the platform when a worker runs:

| Entry | Task | When |
|---|---|---|
| morning-briefing | `productivity.generate_morning_briefing` | 06:00 |
| eod-wrap-up | `productivity.generate_eod_wrap_up` | 18:00 |
| daily-report | `reports.generate_daily_report` | 21:00 |
| weekly-report | `reports.generate_weekly_report` | Mon 07:00 |
| notification-sweep | `notifications.notification_sweep` | hourly |
| github-refresh | `github.refresh_github_analytics` | hourly |
| intelligence-freshness | `intelligence.check_freshness` | every 6h (:17) |
| intelligence-morning | `intelligence.daily_intelligence` | 05:30 |
| intelligence-evening | `intelligence.evening_review` | 22:00 |

The three `intelligence.*` tasks run the engine per user with per-user failure
isolation, so one failing account never blocks the sweep.

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
