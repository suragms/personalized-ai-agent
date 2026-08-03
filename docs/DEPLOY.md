# Deployment

Two supported targets: **Render** (blueprint in `infra/render.yaml`) and any
Docker host. Both build the same images.

## Builds

- `infra/Dockerfile.backend` — Python 3.14-slim, runs gunicorn on :8000.
- `infra/Dockerfile.frontend` — multi-stage: Vite build → nginx serving the SPA
  and proxying `/api` to the backend service.

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

`infra/render.yaml` declares three services:

1. **Postgres** (render postgres with the `vector` extension enabled via a
   start command or pre-created extension).
2. **backend** web service — `gunicorn config.wsgi:application`. Env:
   `SECRET_KEY`, `DATABASE_URL` (or the `POSTGRES_*` vars), `AI_PROVIDER`,
   provider keys, `DJANGO_ALLOWED_HOSTS`.
3. **worker** background service — `celery -A config worker` + beat.
4. **frontend** static site → built with `npm ci && npm run build`, served by
   nginx, with the `/api` proxy target set to the backend service URL via env.

Set environment variables in the Render dashboard (never commit secrets).
Run migrations on deploy: Render **Pre-Deploy** hook →
`python manage.py migrate`.

## CI/CD

`.github/workflows/ci.yml` runs on push/PR:

- **backend job** — installs deps, runs `ruff check`, `pytest`.
- **frontend job** — `npm ci`, `npm run lint`, `npm run test`, `npm run build`.

Postgres is provided by the `pgvector/pgvector:17` service container so the
pytest suite (which uses the real DB) runs in CI.

## Production checklist

- Set a strong `SECRET_KEY`, `DEBUG=False`, and hardened `DJANGO_ALLOWED_HOSTS`.
- Add a real AI provider (`AI_PROVIDER=openai|gemini|ollama`) for generated prose.
- Enable OAuth (`ALLOW_OAUTH=True` + provider client ids) for passwordless login.
- Point Celery at managed Redis; run a worker + beat instance.
- Put the nginx frontend behind HTTPS (Render provides it; add a CDN otherwise).
- Run `python manage.py createsuperuser` for admin access.
