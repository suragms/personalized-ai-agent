"""Google Gemini provider."""
from django.conf import settings

from .base import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def _model(self):
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        return genai.GenerativeModel(settings.GEMINI_MODEL)

    def is_available(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        model = self._model()
        response = model.generate_content(f"{system}\n\n{user}", generation_config=dict(temperature=temperature))
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

        genai.configure(api_key=settings.GEMINI_API_KEY)
        result = genai.embed_content(model="models/embedding-001", content=text)
        return result["embedding"]
