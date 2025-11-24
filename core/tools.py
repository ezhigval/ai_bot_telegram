"""Инструменты агента: веб-поиск, анализ файлов, мультимодальность."""

import os
from abc import ABC, abstractmethod
from typing import Any

import httpx


class Tool(ABC):
    """Базовый интерфейс инструмента."""

    @abstractmethod
    def name(self) -> str:
        """Имя инструмента."""

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> str:
        """Выполнить инструмент и вернуть результат."""


class WebSearchTool(Tool):
    """Веб-поиск через бесплатные API (DuckDuckGo)."""

    def name(self) -> str:
        return "web_search"

    async def execute(self, input_data: dict[str, Any]) -> str:
        """Поиск в интернете через DuckDuckGo."""
        query = input_data.get("query", "")
        if not query:
            return "Ошибка: не указан поисковый запрос."

        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                abstract = data.get("AbstractText", "")
                if abstract:
                    return f"Результат поиска по запросу '{query}':\n\n{abstract}"

                related = data.get("RelatedTopics", [])
                if related:
                    first_result = related[0].get("Text", "")
                    if first_result:
                        return f"Результат поиска по запросу '{query}':\n\n{first_result}"

                return f"По запросу '{query}' ничего не найдено."

        except httpx.HTTPError as e:
            return f"Ошибка при поиске: {e}"
        except Exception as e:
            return f"Неожиданная ошибка при поиске: {e}"


class FileAnalysisTool(Tool):
    """Базовый анализ файлов (пока заглушка, позже добавим реальную обработку)."""

    def name(self) -> str:
        return "file_analysis"

    async def execute(self, input_data: dict[str, Any]) -> str:
        """Анализ файла по метаданным."""
        file_name = input_data.get("file_name", "неизвестный файл")
        mime_type = input_data.get("mime_type", "")
        file_size = input_data.get("file_size", 0)

        size_mb = file_size / (1024 * 1024) if file_size else 0
        return (
            f"Файл получен:\n"
            f"• Имя: {file_name}\n"
            f"• Тип: {mime_type}\n"
            f"• Размер: {size_mb:.2f} MB\n\n"
            f"Полный анализ файлов будет добавлен позже (PDF, таблицы, документы)."
        )


class MediaAnalysisTool(Tool):
    """Анализ медиа (изображения, видео) через локальные модели или API."""

    def name(self) -> str:
        return "media_analysis"

    async def execute(self, input_data: dict[str, Any]) -> str:
        """Анализ медиа-файла."""
        media_type = input_data.get("media_type", "")
        file_id = input_data.get("file_id", "")

        if media_type == "image":
            return (
                f"Изображение получено (ID: {file_id}).\n"
                f"Анализ изображений через vision-модели будет добавлен позже."
            )
        elif media_type == "video":
            duration = input_data.get("duration", 0)
            return (
                f"Видео получено (ID: {file_id}, длительность: {duration} сек).\n"
                f"Анализ видео будет добавлен позже."
            )
        elif media_type == "voice":
            duration = input_data.get("duration", 0)
            return (
                f"Голосовое сообщение получено (ID: {file_id}, длительность: {duration} сек).\n"
                f"Распознавание речи будет добавлено позже."
            )

        return f"Медиа-файл получен, но тип '{media_type}' не поддерживается."


class ToolRouter:
    """Маршрутизатор инструментов: выбирает нужный инструмент по контексту."""

    def __init__(self) -> None:
        self.tools: dict[str, Tool] = {
            "web_search": WebSearchTool(),
            "file_analysis": FileAnalysisTool(),
            "media_analysis": MediaAnalysisTool(),
        }

    async def route(self, context: dict[str, Any]) -> str:
        """
        Выбрать и выполнить подходящий инструмент.

        Args:
            context: Контекст запроса (тип сообщения, данные и т.д.)

        Returns:
            Результат выполнения инструмента
        """
        # Если есть явный запрос на поиск
        text = context.get("text", "").lower()
        if any(keyword in text for keyword in ["найди", "поиск", "найти", "search", "find"]):
            return await self.tools["web_search"].execute({"query": context.get("text", "")})

        # Если есть медиа
        if context.get("media_type"):
            media_data = context.get("media_data", {})
            media_data["media_type"] = context.get("media_type")
            return await self.tools["media_analysis"].execute(media_data)

        # Если есть файл
        if context.get("media_type") == "file":
            return await self.tools["file_analysis"].execute(context.get("media_data", {}))

        # По умолчанию ничего не делаем
        return ""
