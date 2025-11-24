import asyncio
import logging
import os
from typing import Final

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tg_bot")

CORE_BASE_URL: Final[str] = os.getenv("CORE_BASE_URL", "http://localhost:8000")


async def call_core(text: str | None, user_id: int) -> str:
    url = f"{CORE_BASE_URL.rstrip('/')}/v1/messages"
    payload = {
        "user_id": str(user_id),
        "channel": "telegram",
        "text": text,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return str(data.get("text") or "")
    except Exception as exc:  # noqa: BLE001
        logger.error("Ошибка при обращении к ядру: %s", exc)
        # Фоллбэк: простое эхо, чтобы бот продолжал работать
        return f"Эхо (ядро недоступно): {text or ''}"


async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Я Telegram-оболочка над локальным ИИ-ядром.\n"
        "Сейчас я подключен к Python-ядру и постепенно становлюсь умнее.\n"
        "Напиши мне сообщение — я прокину его в ядро и пришлю ответ."
    )


async def handle_text(message: Message) -> None:
    reply = await call_core(message.text, message.from_user.id)
    await message.answer(reply or "Пустой ответ от ядра.")


async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")

    bot = Bot(token=token)
    dp = Dispatcher()

    dp.message.register(handle_start, CommandStart())
    dp.message.register(handle_text, lambda m: isinstance(m, types.Message) and m.text)

    logger.info("Starting Telegram bot...")
    logger.info("CORE_BASE_URL=%s", CORE_BASE_URL)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


