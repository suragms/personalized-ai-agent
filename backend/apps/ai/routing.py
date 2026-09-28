import logging
import time
from django.conf import settings
from django.utils import timezone
from .models import ProviderConnection
from .adapters import instantiate_adapter
from .exceptions import AIProviderError

logger = logging.getLogger("ai")

class AIRoutingService:
    def __init__(self, user):
        self.user = user

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

    def _normalize_and_throw(self, exc):
        exc_str = str(exc).lower()
        if "timeout" in exc_str:
            return "TIMEOUT", "Connection to provider timed out."
        if "incorrect api key" in exc_str or "unauthorized" in exc_str or "401" in exc_str:
            return "INVALID_CREDENTIALS", "Invalid API credentials."
        if "rate limit" in exc_str or "429" in exc_str:
            return "RATE_LIMITED", "Provider rate limit exceeded."
        if "not found" in exc_str or "404" in exc_str:
            return "MODEL_NOT_FOUND", "Requested model not found or base URL invalid."
        if "refused" in exc_str or "connection error" in exc_str:
            return "CONNECTION_REFUSED", "Could not connect to provider."
        return "SERVER_ERROR", f"Provider error: {exc}"

    def execute_with_fallback(self, fn_name, *args, **kwargs):
        conns = self._get_connections_to_try()
        
        # Fallback to system mock if nothing exists
        if not conns:
            p = instantiate_adapter("mock")
            return getattr(p, fn_name)(*args, **kwargs)
            
        last_error = None
        for conn in conns:
            try:
                adapter = self._get_adapter(conn)
                if not adapter.is_available():
                    continue
                return getattr(adapter, fn_name)(*args, **kwargs)
            except Exception as e:
                code, detail = self._normalize_and_throw(e)
                last_error = {"code": code, "detail": detail}
                
                # Do not retry on invalid credentials or if model lacks permissions
                if code in ["INVALID_CREDENTIALS"]:
                    break
                    
                logger.warning(f"Failed via {conn.display_name} ({code}), trying next config.")
        
        # If all fail or we broke out
        if last_error:
            raise AIProviderError(last_error["code"], last_error["detail"])
        raise AIProviderError("PROVIDER_UNAVAILABLE", "No available providers.")

    def complete(self, *args, **kwargs):
        return self.execute_with_fallback('complete', *args, **kwargs)
        
    def chat(self, *args, **kwargs):
        return self.execute_with_fallback('chat', *args, **kwargs)

    def embed(self, *args, **kwargs):
        return self.execute_with_fallback('embed', *args, **kwargs)

    def test_connection(self, conn: ProviderConnection):
        adapter = self._get_adapter(conn)
        start = time.time()
        try:
            adapter.complete("You are a helpful assistant.", "Say 'ok'.", max_tokens=2, temperature=0)
            latency = int((time.time() - start) * 1000)
            
            conn.last_tested_at = timezone.now()
            conn.latency_ms = latency
            conn.last_error_code = ""
            conn.save(update_fields=['last_tested_at', 'latency_ms', 'last_error_code'])
            
            return {"status": "ok", "latency_ms": latency}
        except Exception as e:
            code, detail = self._normalize_and_throw(e)
            conn.last_tested_at = timezone.now()
            conn.last_error_code = code
            conn.latency_ms = None
            conn.save(update_fields=['last_tested_at', 'last_error_code', 'latency_ms'])
            return {"status": "error", "code": code, "detail": detail}

