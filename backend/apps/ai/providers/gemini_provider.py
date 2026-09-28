"""Google Gemini provider."""
from django.conf import settings

from .base import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def _model(self):
        import google.generativeai as genai

        api_key = self.api_key or getattr(settings, "GEMINI_API_KEY", "")
        model_name = self.model or getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)

    def is_available(self) -> bool:
        return bool(self.api_key or getattr(settings, "GEMINI_API_KEY", ""))

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        model = self._model()
        generation_config = dict(temperature=temperature)
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        prompt = f"{system}\n\n{user}" if system else user
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text

    def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        # Gemini uses a flat conversation; system prompt is folded into the first turn.
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        turns = [m for m in messages if m.get("role") != "system"]
        prompt = f"{system}\n\n" if system else ""
        prompt += "\n\n".join(f"{m['role']}: {m['content']}" for m in turns)
        return self.complete("", prompt, temperature=temperature, max_tokens=max_tokens)

    def embed(self, text: str) -> list[float]:
        import google.generativeai as genai

        api_key = self.api_key or getattr(settings, "GEMINI_API_KEY", "")
        genai.configure(api_key=api_key)
        embed_model = getattr(settings, "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
        try:
            result = genai.embed_content(model=embed_model, content=text)
            return result["embedding"]
        except Exception:
            try:
                result = genai.embed_content(model="models/embedding-001", content=text)
                return result["embedding"]
            except Exception:
                # Return empty/fallback vector if API embedding fails
                return []
