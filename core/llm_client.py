"""Абстракция для работы с LLM (локальные модели через Ollama)."""

import httpx
import os
from typing import Any


class LLMClient:
    """Клиент для локального LLM через Ollama."""

    def __init__(self, base_url: str | None = None, model: str = "llama3.2") -> None:
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = 60.0

    async def generate(
        self, prompt: str, system: str | None = None, history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Сгенерировать ответ от LLM.

        Args:
            prompt: Пользовательский запрос
            system: Системный промпт (опционально)
            history: История диалога в формате [{"role": "user", "content": "..."}, ...]

        Returns:
            Сгенерированный текст ответа
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url.rstrip('/')}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return str(data.get("message", {}).get("content", ""))
        except httpx.HTTPError as e:
            # Если Ollama недоступна, возвращаем умную заглушку
            return f"[LLM недоступен: {e}] Пока я работаю без локальной модели. Установи Ollama и запусти модель {self.model}, чтобы я стал умнее."
        except Exception as e:
            return f"[Ошибка LLM: {e}] Попробуй позже."
