"""Модели данных для ядра ИИ."""

from dataclasses import dataclass
from typing import Any


@dataclass
class MessageIn:
    """Входящее сообщение от клиента."""

    user_id: str
    channel: str  # "telegram" | "mac_client"
    text: str | None = None
    media_type: str | None = None  # "image" | "video" | "voice" | "file"
    media_data: dict[str, Any] | None = None  # метаданные медиа


@dataclass
class MessageOut:
    """Исходящий ответ агента."""

    text: str
    media_type: str | None = None
    media_data: dict[str, Any] | None = None


@dataclass
class UserProfile:
    """Профиль пользователя."""

    user_id: str
    telegram_id: str | None = None
    mac_username: str | None = None
    language: str = "ru"
    tone: str = "friendly"  # "friendly" | "formal" | "casual"
    response_format: str = "text"  # "text" | "voice" | "auto"
