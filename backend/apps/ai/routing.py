import logging
import time

from django.utils import timezone

from core.connectivity import (
    AI_PROVIDER_NOT_CONFIGURED,
    AI_PROVIDER_UNKNOWN_ERROR,
    ConnectivityStatus,
    ai_error_code,
    normalize_exception,
    sanitize_error_message,
)

from .adapters import instantiate_adapter
from .exceptions import AIProviderError
from .models import ProviderConnection

logger = logging.getLogger("ai")

# Provenance values (see core audit §11): what actually produced a response.
PROVENANCE_REAL = "REAL_AI_PROVIDER"
PROVENANCE_MOCK = "MOCK_PROVIDER"
PROVENANCE_TEMPLATE = "DETERMINISTIC_TEMPLATE"


class AIRoutingService:
    def __init__(self, user):
        self.user = user
        # Set on each successful execute_with_fallback call so callers can
        # record provenance (which provider actually produced the output).
        self.last_provider: str | None = None
        self.last_provenance: str | None = None

    def _get_connections_to_try(self):
        conns = list(ProviderConnection.objects.filter(owner=self.user, enabled=True))
        if not conns:
            return []

        default = next((c for c in conns if c.is_default), None)
        if default:
            conns.remove(default)
            conns.insert(0, default)

        return conns

    def _get_adapter(self, conn: ProviderConnection):
        return instantiate_adapter(
            conn.provider.protocol,
            api_key=conn.api_key,
            base_url=conn.base_url,
            model=conn.model
        )

    def _mark_unavailable(self, conn: ProviderConnection, detail: str):
        conn.status = ConnectivityStatus.NOT_CONFIGURED.value
        conn.last_error_code = "not_configured"
        conn.last_error_message = sanitize_error_message(detail)
        conn.retryable = True
        conn.last_tested_at = timezone.now()
        conn.save(update_fields=['status', 'last_error_code', 'last_error_message', 'retryable', 'last_tested_at'])

    def execute_with_fallback(self, fn_name, *args, **kwargs):
        conns = self._get_connections_to_try()

        # Fallback to system mock if nothing is configured. The mock is a
        # deterministic offline provider — provenance is recorded so callers
        # never present its output as external AI output.
        if not conns:
            p = instantiate_adapter("mock")
            self.last_provider = "mock"
            self.last_provenance = PROVENANCE_MOCK
            logger.info("AI request served by mock provider (no provider connections configured).")
            return getattr(p, fn_name)(*args, **kwargs)

        last_error = None
        skipped_any = False
        for conn in conns:
            try:
                adapter = self._get_adapter(conn)
                if not adapter.is_available():
                    skipped_any = True
                    self._mark_unavailable(conn, f"Provider '{conn.provider_id}' is not configured or unreachable.")
                    continue
                result = getattr(adapter, fn_name)(*args, **kwargs)
                self.last_provider = conn.provider_id
                self.last_provenance = PROVENANCE_MOCK if conn.provider_id == "mock" else PROVENANCE_REAL
                return result
            except Exception as e:
                status, retryable, code = normalize_exception(e)
                detail = sanitize_error_message(e)
                last_error = {"code": ai_error_code(status, code), "detail": detail}

                # Update connection state in the DB
                conn.status = status.value
                conn.last_error_code = code
                conn.last_error_message = detail
                conn.retryable = retryable
                conn.last_tested_at = timezone.now()
                conn.save(update_fields=['status', 'last_error_code', 'last_error_message', 'retryable', 'last_tested_at'])

                # Do not retry on invalid credentials or if model lacks permissions
                if not retryable:
                    break

                logger.warning(f"Failed via {conn.display_name} ({code}), trying next config.")

        # If all fail or we broke out
        if last_error:
            raise AIProviderError(last_error["code"], last_error["detail"])
        if skipped_any:
            raise AIProviderError(AI_PROVIDER_NOT_CONFIGURED, "No configured provider is available.")
        raise AIProviderError(AI_PROVIDER_UNKNOWN_ERROR, "No available providers.")

    def complete(self, *args, **kwargs):
        return self.execute_with_fallback('complete', *args, **kwargs)

    def chat(self, *args, **kwargs):
        return self.execute_with_fallback('chat', *args, **kwargs)

    def embed(self, *args, **kwargs):
        return self.execute_with_fallback('embed', *args, **kwargs)

    def test_connection(self, conn: ProviderConnection):
        start = time.time()
        try:
            adapter = self._get_adapter(conn)
        except Exception as e:
            status, retryable, code = normalize_exception(e)
            self._record_test_failure(conn, status, code, e)
            return {"status": "error", "code": ai_error_code(status, code), "detail": sanitize_error_message(e)}

        if not adapter.is_available():
            self._mark_unavailable(conn, f"Provider '{conn.provider_id}' is not configured or unreachable.")
            return {
                "status": "error",
                "code": AI_PROVIDER_NOT_CONFIGURED,
                "detail": f"Provider '{conn.provider_id}' is not configured or unreachable.",
            }

        try:
            adapter.complete("You are a helpful assistant.", "Say 'ok'.", max_tokens=2, temperature=0)
            latency = int((time.time() - start) * 1000)

            conn.last_tested_at = timezone.now()
            conn.latency_ms = latency
            conn.status = ConnectivityStatus.CONNECTED.value
            conn.last_error_code = ""
            conn.last_error_message = ""
            conn.retryable = False
            conn.save(update_fields=['last_tested_at', 'latency_ms', 'status', 'last_error_code', 'last_error_message', 'retryable'])

            return {"status": "ok", "latency_ms": latency}
        except Exception as e:
            status, retryable, code = normalize_exception(e)
            self._record_test_failure(conn, status, code, e)
            return {
                "status": "error",
                "code": ai_error_code(status, code),
                "detail": sanitize_error_message(e),
                "retryable": retryable,
            }

    def _record_test_failure(self, conn: ProviderConnection, status: ConnectivityStatus, code: str, exc: Exception):
        detail = sanitize_error_message(exc)
        retryable = status in (
            ConnectivityStatus.TIMEOUT,
            ConnectivityStatus.RATE_LIMITED,
            ConnectivityStatus.NETWORK_ERROR,
            ConnectivityStatus.SERVICE_UNAVAILABLE,
        )
        conn.last_tested_at = timezone.now()
        conn.status = status.value
        conn.last_error_code = code
        conn.last_error_message = detail
        conn.retryable = retryable
        conn.latency_ms = None
        conn.save(update_fields=['last_tested_at', 'status', 'last_error_code', 'last_error_message', 'retryable', 'latency_ms'])
