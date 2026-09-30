# API Reference

Base URL: `/api/`. All endpoints except auth/health require
`Authorization: Bearer <access>`.

## Auth (`/api/auth/`)

| Method | Path | Body / Query | Description |
|---|---|---|---|
| POST | `login/` | `{username, password}` | JWT pair + user |
| POST | `refresh/` | `{refresh}` | Rotate access token |
| POST | `register/` | `{username, email, password}` | First account becomes OWNER |
| GET | `me/` | — | Current user |
| POST | `oauth/github/` | `{code, redirect_uri}` | GitHub code-exchange (needs `ALLOW_OAUTH`) |
| POST | `oauth/google/` | `{code, redirect_uri}` | Google code-exchange |

## GitHub (`/api/github/`)

| Method | Path | Description |
|---|---|---|
| GET | `repos/` | Repositories + health/status |
| GET | `commits/?repository=` | Commits (optionally filtered) |
| GET | `pull-requests/` · `issues/` · `releases/` | Listings |
| GET | `analytics/?weeks=8` | Weekly totals, daily series, per-repo summary, productivity score |
| GET | `health/` | At-risk / inactive repositories |
| GET | `insights/` | Generated recommendations |
| GET | `contributions/?days=90` | Daily commit counts (heatmap) |

## Productivity (`/api/`)

| Method | Path | Description |
|---|---|---|
| CRUD | `tasks/` | Task list/create/update (status, priority) |
| CRUD | `calendar/` | Calendar events |
| CRUD | `focus-sessions/` | Focus sessions |
| GET | `briefings/?kind=morning\|eod` | Generated briefings |
| POST | `briefings/generate/` | `{kind}` → generate (idempotent per day) |
| GET | `productivity/score/` | Today's productivity score |

## Projects (`/api/projects/`)

| Method | Path | Description |
|---|---|---|
| CRUD | `projects/` | Projects (completion %, risk, velocity, delivery, burndown computed) |
| POST | `projects/<id>/snapshot/` | Record a progress snapshot |
| GET | `projects/<id>/metrics/` | Full metric payload |
| GET | `burndown/overview/` | Burndown series for all projects |
| CRUD | `milestones/` | Milestones |

## Intelligence (`/api/intelligence/`)

| Method | Path | Description |
|---|---|---|
| CRUD | `data-sources/` | Connected data sources (state, freshness, sync cadence) |
| POST | `data-sources/<id>/sync/` | Dispatch a real sync (`400 sync_unsupported` / `400 not_connected` / `502 sync_failed`) |
| GET | `data-snapshots/` | Point-in-time captures (content-hashed) |
| CRUD | `insights/` | Evidence-backed insights (`?status=new`, excludes dismissed/completed/expired) |
| POST | `insights/generate/` | Run the Intelligence Engine now; returns `created/updated/expired/tasks_created/alerts_created/interpreted/…` |
| POST | `insights/<id>/convert_to_task/` | Explicitly convert a recommendation into a `Task` (dedup-keyed) |
| POST | `insights/<id>/mark_helpful/` · `dismiss/` | Feedback / dismiss |
| CRUD | `alerts/` | Alerts (dedup + 24h cooldown; dismissed never re-raised) |
| POST | `alerts/<id>/mark_read/` · `resolve/` | Alert lifecycle |
| CRUD | `goals/` · `decisions/` | Goals and decision framework |
| GET/POST | `reports/`, `reports/generate/` | `generate` returns `400 insufficient_data` instead of fabricating a report |
| GET | `performance/` | Performance metrics (only recorded when data exists) |
| GET | `daily-plans/today/` · POST `daily-plans/generate/` | Morning brief / evening review (deterministic, idempotent per day) |
| GET/PUT | `profile/me/` | Onboarding profile |
| CRUD | `integrations/` · POST `integrations/<id>/disconnect/` | OAuth connections |
| GET | `summary/` | Engine counts (insights by severity/status, active alerts) + per-source freshness + data health |
| GET | `data-health/` | Per-source freshness in the `fresh`/`aging`/`stale`/`unavailable` vocabulary |

Provenance values on insights/reports/tasks: `REAL_CONNECTED_DATA`, `USER_PROVIDED_DATA`,
`AI_DERIVED_ANALYSIS`, `STALE_DATA`, `UNAVAILABLE_DATA`, `ERROR`, plus AI prose provenance
`REAL_AI_PROVIDER` / `MOCK_PROVIDER` / `DETERMINISTIC_TEMPLATE`. `confidence` may be `insufficient`.

## Reports (`/api/reports/`)

| Method | Path | Description |
|---|---|---|
| GET | `reports/?period=` | Generated reports |
| POST | `reports/generate/` | `{period: daily\|weekly\|…\|client}` |
| GET | `reports/<id>/export/?format=` | `md` \| `html` \| `pdf` \| `xlsx` \| `docx` |

## LinkedIn (`/api/linkedin/`)

| Method | Path | Description |
|---|---|---|
| GET/PUT | `profile/` | Owner's LinkedIn profile |
| GET | `analyze/` | Score + breakdown + suggestions |
| GET | `posts/` | Post ideas |
| POST | `posts/generate/` | Draft a post from recent work |
| GET | `posting-time/` | Recommended windows |
| GET | `score-history/` | Score over time |

## Resume (`/api/resume/`)

| Method | Path | Description |
|---|---|---|
| GET | `latest/` | Latest version |
| POST | `versions/regenerate/` | Build a new version from activity |
| GET | `versions/<id>/export/?format=pdf\|docx` | Download |

## Portfolio (`/api/portfolio/`)

| Method | Path | Description |
|---|---|---|
| CRUD | `projects/` | Portfolio projects |
| POST | `projects/refresh/` | Re-sync from GitHub repos |
| GET/PUT | `settings/` | Portfolio settings |

## Learning (`/api/learning/`)

| Method | Path | Description |
|---|---|---|
| CRUD | `items/` | Tracked items; `POST items/<id>/complete/` |
| GET/POST | `suggestions/` | Daily suggestions (POST regenerates) |
| GET | `roadmap/` | Personal roadmap |
| GET | `trends/` | Trending topics |

## Analytics (`/api/analytics/<module>/`)

`overview` · `coding` · `projects` · `time` · `learning` · `linkedin` · `resume` · `business`
(+ `/history/` for cached snapshots)

## Notifications (`/api/notifications/`)

| Method | Path | Description |
|---|---|---|
| GET | `notifications/?unread=1` | Feed |
| POST | `notifications/<id>/read/` · `mark_all_read/` | Mark read |
| POST | `sweep/` | Run the rule sweep now |
| GET | `unread/` | Unread count |
| CRUD | `rules/` | Notification rules |

## AI Assistant (`/api/ai/`)

| Method | Path | Description |
|---|---|---|
| POST | `command/` | `{command}` → matched intent + agent response |
| GET | `providers/` | Provider status (Settings page) |

## Memory (`/api/memory/`)

| Method | Path | Description |
|---|---|---|
| CRUD | `memory/` | Memory entries (with embeddings) |
| GET | `search/?query=&k=` | Search with `mode`/`message`: `semantic` only when pgvector + a real embedding provider are available, otherwise an honest keyword/recent fallback |
| GET/POST | `conversations/` | Conversation log |
| GET/PUT | `preferences/` | User preferences |

## Health (`/api/health/`)

`GET /api/health/` — unauthenticated, credential-free, safe to poll.

```json
{
  "status": "ok",
  "services": {
    "database":  {"status": "connected"},
    "redis":     {"status": "connected"},
    "celery":    {"status": "running"},
    "ai_provider": {"status": "configured", "mode": "mock"},
    "github":    {"status": "configured"},
    "google":    {"status": "not_configured"}
  },
  "integrations": { "github": {"status": "connected"}, "linkedin": {"status": "not_configured"} }
}
```

- `status` is `ok` | `degraded` (top level) and lowercase snake_case per check.
- `integrations` is included only for authenticated requests (per-user state).
- Returns `503` only when the database itself is unreachable.
- Probes never echo secrets or credentials.
