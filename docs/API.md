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
| GET | `search/?query=&k=` | Semantic (pgvector) search |
| GET/POST | `conversations/` | Conversation log |
| GET/PUT | `preferences/` | User preferences |

## Health (`/api/health/`)

`GET /api/health/` → `{"status": "ok", "database": "connected"}` (unauthenticated).
