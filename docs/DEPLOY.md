# Deployment

Two supported targets: **Render** (blueprint in `infra/render.yaml`) and any
Docker host. Both build the same images.

## Builds

- `infra/Dockerfile.backend` — Python 3.14-slim, runs gunicorn on :8000.
- `infra/Dockerfile.frontend` — multi-stage: Vite build → nginx serving the SPA
  and proxying `/api` and `/ws` (WebSocket) to the backend service.

Local image build:

```bash
docker build -f infra/Dockerfile.backend -t agent-backend .
docker build -f infra/Dockerfile.frontend -t agent-frontend .
```

## Docker Compose (full stack)

Extend `infra/docker-compose.yml` with `backend` and `frontend` services that
point at the images, plus environment from `.env`. nginx in the frontend image
proxies `/api` to `http://backend:8000`.

## Render

`infra/render.yaml` declares five services:

1. **Postgres** (`agent-postgres`).
2. **Redis** (`agent-redis`) — broker, result backend, and channel layer.
3. **backend** web service — `gunicorn config.wsgi:application` on :8000.
   Env: `SECRET_KEY` (auto-generated), `ENCRYPTION_KEY` (**required — set a
   Fernet key in the dashboard after import or the app refuses to boot**),
   `POSTGRES_*` (from the database), `REDIS_URL` / `CELERY_RESULT_BACKEND`
   (from the Redis service), `AI_PROVIDER`, `CORS_ALLOWED_ORIGINS`,
   `DJANGO_ALLOWED_HOSTS`.
4. **worker** background service — `celery -A config worker --beat`.
5. **frontend** static site — `npm ci && npm run build`, published from
   `dist`, talking to the backend cross-origin via `VITE_API_BASE`.

Set `ENCRYPTION_KEY` in the Render dashboard (never commit secrets):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Run migrations on deploy: Render **Pre-Deploy** hook →
`python manage.py migrate`.

> WebSockets (`/ws/notifications/`): Render's static frontend cannot proxy
> them — the SPA connects directly to the backend origin using
> `VITE_API_BASE`. For the Docker path, nginx proxies both `/api/` and
> `/ws/` (see `infra/nginx.conf`).

## CI/CD

`.github/workflows/ci.yml` runs on push/PR:

- **backend job** — installs deps, runs `ruff check`, `pytest`.
- **frontend job** — `npm ci`, `npm run lint`, `npm run test`, `npm run build`.

Postgres is provided by the `pgvector/pgvector:17` service container so the
pytest suite (which uses the real DB) runs in CI.

## Production checklist

- Set a strong `SECRET_KEY`, `DEBUG=False`, and hardened `DJANGO_ALLOWED_HOSTS`.
- Set `ENCRYPTION_KEY` (Fernet) — required; protects stored provider credentials.
- Set `CORS_ALLOWED_ORIGINS` to the exact frontend origin(s).
- Add a real AI provider (`AI_PROVIDER=openai|gemini|ollama|groq`) for generated prose.
- Enable OAuth (`ALLOW_OAUTH=True` + provider client ids) for passwordless login.
- Point Celery at managed Redis; run a worker + beat instance.
- Put the nginx frontend behind HTTPS (Render provides it; add a CDN otherwise).
- Run `python manage.py createsuperuser` (or `init_admin --password <pw>`) for admin access.
