"""
Django settings for the Personal AI Agent platform.

Configuration is read from environment variables (with .env support) so the
same codebase runs locally, in Docker, and on Render without modification.
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load .env from the repository root first, then the backend directory.
load_dotenv(REPO_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

# Make app modules importable as top-level packages (e.g. `accounts`, `github`).
sys.path.insert(0, str(BASE_DIR / "apps"))

# ── Environment helper ────────────────────────────────────────────────────
def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# ── Core Django ───────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "corsheaders",
    "rest_framework",
    "channels",
    # Platform apps
    "core",
    "accounts",
    "ai",
    "memory",
    "github",
    "productivity",
    "projects",
    "reports",
    "linkedin",
    "resume",
    "portfolio",
    "learning",
    "analytics",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Database (PostgreSQL + pgvector) ──────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "agent_db"),
        "USER": os.getenv("POSTGRES_USER", "agent"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "agent"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5433"),
        "OPTIONS": {"connect_timeout": 10},
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/api/auth/login"

# ── Django REST Framework ─────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── CORS ──────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
)
CORS_ALLOW_CREDENTIALS = True

# ── Channel Layer (WebSocket backing store) ───────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    } if not env_bool("USE_IN_MEMORY_CHANNELS", False) else {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ── Celery / Redis ────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {
    "morning-briefing": {
        "task": "productivity.tasks.generate_morning_briefing",
        "schedule": timedelta(hours=24),
        "kwargs": {"hour": 6},
    },
    "eod-wrap-up": {
        "task": "productivity.tasks.generate_eod_wrap_up",
        "schedule": timedelta(hours=24),
        "kwargs": {"hour": 18},
    },
    "daily-report": {
        "task": "reports.tasks.generate_daily_report",
        "schedule": timedelta(hours=24),
        "kwargs": {"hour": 21},
    },
    "weekly-report": {
        "task": "reports.tasks.generate_weekly_report",
        "schedule": timedelta(days=7),
    },
    "notification-sweep": {
        "task": "notifications.tasks.notification_sweep",
        "schedule": timedelta(hours=1),
    },
    "github-refresh": {
        "task": "github.tasks.refresh_github_analytics",
        "schedule": timedelta(hours=1),
    },
}

# ── AI layer ──────────────────────────────────────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")  # mock | ollama | openai | gemini
AI_EMBEDDING_DIM = int(os.getenv("AI_EMBEDDING_DIM", "384"))
AI_ENHANCE_PROSE = env_bool("AI_ENHANCE_PROSE", False)  # LLM prose when a real provider is set

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# ── OAuth / signup ────────────────────────────────────────────────────────
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
ALLOW_OAUTH = env_bool("ALLOW_OAUTH", False)
ALLOW_SIGNUP = env_bool("ALLOW_SIGNUP", True)

# ── Notifications ─────────────────────────────────────────────────────────
NOTIFY_EMAIL_FROM = os.getenv("NOTIFY_EMAIL_FROM", "")
NOTIFY_TELEGRAM_BOT_TOKEN = os.getenv("NOTIFY_TELEGRAM_BOT_TOKEN", "")
NOTIFY_TELEGRAM_CHAT_ID = os.getenv("NOTIFY_TELEGRAM_CHAT_ID", "")

# ── Internationalization / static ─────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Logging ───────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "ai": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "agents": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# ── Sentry Error Tracking ────────────────────────────────────────────────
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG and os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
    )

