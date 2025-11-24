"""Ядро ИИ-агента: обработка запросов, вызов LLM, использование памяти и инструментов."""

from core.llm_client import LLMClient
from core.memory import Memory
from core.models import MessageIn, MessageOut, UserProfile
from core.tools import ToolRouter


class Agent:
    """Основной агент, обрабатывающий запросы пользователей."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        memory: Memory | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        self.memory = memory or Memory()
        self.tool_router = ToolRouter()

    async def process(self, msg_in: MessageIn) -> MessageOut:
        """
        Обработать входящее сообщение и вернуть ответ.

        Args:
            msg_in: Входящее сообщение

        Returns:
            Ответ агента
        """
        # Получаем или создаём профиль пользователя
        profile = self.memory.get_or_create_profile(msg_in.user_id)

        # Обновляем профиль, если пришли новые данные
        if msg_in.channel == "telegram":
            self.memory.update_profile(msg_in.user_id, telegram_id=msg_in.user_id)
        elif msg_in.channel == "mac_client":
            # TODO: извлечь mac_username из msg_in, когда появится
            pass

        # Проверяем, нужен ли инструмент (поиск, анализ медиа и т.д.)
        tool_result = await self.tool_router.route({
            "text": msg_in.text,
            "media_type": msg_in.media_type,
            "media_data": msg_in.media_data,
        })

        # Получаем контекст из истории
        history = self.memory.get_recent_history(msg_in.user_id, limit=5)
        history_messages = []
        for hist_in, hist_out in history:
            if hist_in.text:
                history_messages.append({"role": "user", "content": hist_in.text})
            if hist_out.text:
                history_messages.append({"role": "assistant", "content": hist_out.text})

        # Формируем системный промпт с учётом профиля
        system_prompt = self._build_system_prompt(profile)

        # Формируем промпт для LLM (включая результат инструмента, если есть)
        user_text = msg_in.text or "[медиа-сообщение без текста]"
        if tool_result:
            user_text = f"{user_text}\n\n[Контекст от инструмента: {tool_result}]"

        # Генерируем ответ через LLM
        response_text = await self.llm.generate(
            prompt=user_text,
            system=system_prompt,
            history=history_messages if history_messages else None,
        )

        msg_out = MessageOut(text=response_text)

        # Сохраняем взаимодействие в память
        self.memory.save_interaction(msg_in, msg_out)

        return msg_out

    def _build_system_prompt(self, profile: UserProfile) -> str:
        """Построить системный промпт с учётом профиля пользователя."""
        tone_map = {
            "friendly": "дружелюбный, неформальный",
            "formal": "формальный, вежливый",
            "casual": "непринуждённый, разговорный",
        }
        tone_desc = tone_map.get(profile.tone, "дружелюбный")

        return f"""Ты — персональный ИИ-ассистент. Твоя задача — помогать пользователю в любых вопросах.

Тон общения: {tone_desc}
Язык: {profile.language}

Будь полезным, точным и дружелюбным. Если не знаешь ответа — честно скажи об этом.
Используй информацию от инструментов (веб-поиск, анализ файлов), если она предоставлена в контексте."""
