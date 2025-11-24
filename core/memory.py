"""Память агента: хранение диалогов и профилей пользователей."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from core.models import MessageIn, MessageOut, UserProfile


class Memory:
    """Простая SQLite-память для диалогов и профилей."""

    def __init__(self, db_path: str = "data/core.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Инициализация таблиц БД."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY,
                telegram_id TEXT,
                mac_username TEXT,
                language TEXT DEFAULT 'ru',
                tone TEXT DEFAULT 'friendly',
                response_format TEXT DEFAULT 'text',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                message_type TEXT NOT NULL,
                input_text TEXT,
                output_text TEXT,
                input_media TEXT,
                output_media TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES profiles(user_id)
            )
            """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)"
        )

        conn.commit()
        conn.close()

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Получить или создать профиль пользователя."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            profile = UserProfile(
                user_id=row[0],
                telegram_id=row[1],
                mac_username=row[2],
                language=row[3] or "ru",
                tone=row[4] or "friendly",
                response_format=row[5] or "text",
            )
        else:
            profile = UserProfile(user_id=user_id)
            cursor.execute(
                """
                INSERT INTO profiles (user_id, language, tone, response_format)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, profile.language, profile.tone, profile.response_format),
            )
            conn.commit()

        conn.close()
        return profile

    def update_profile(
        self,
        user_id: str,
        telegram_id: str | None = None,
        mac_username: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Обновить профиль пользователя."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updates = []
        values = []

        if telegram_id is not None:
            updates.append("telegram_id = ?")
            values.append(telegram_id)
        if mac_username is not None:
            updates.append("mac_username = ?")
            values.append(mac_username)
        for key, value in kwargs.items():
            if key in ("language", "tone", "response_format"):
                updates.append(f"{key} = ?")
                values.append(value)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            cursor.execute(
                f"UPDATE profiles SET {', '.join(updates)} WHERE user_id = ?", values
            )
            conn.commit()

        conn.close()

    def save_interaction(
        self, msg_in: MessageIn, msg_out: MessageOut
    ) -> None:
        """Сохранить взаимодействие в историю."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages (user_id, channel, message_type, input_text, output_text, input_media, output_media)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg_in.user_id,
                msg_in.channel,
                msg_in.media_type or "text",
                msg_in.text,
                msg_out.text,
                json.dumps(msg_in.media_data) if msg_in.media_data else None,
                json.dumps(msg_out.media_data) if msg_out.media_data else None,
            ),
        )

        conn.commit()
        conn.close()

    def get_recent_history(
        self, user_id: str, limit: int = 10
    ) -> list[tuple[MessageIn, MessageOut]]:
        """Получить последние N сообщений пользователя."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT channel, message_type, input_text, output_text, input_media, output_media
            FROM messages
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )

        history = []
        for row in reversed(cursor.fetchall()):
            msg_in = MessageIn(
                user_id=user_id,
                channel=row[0],
                text=row[2],
                media_type=row[1] if row[1] != "text" else None,
                media_data=json.loads(row[4]) if row[4] else None,
            )
            msg_out = MessageOut(
                text=row[3] or "",
                media_data=json.loads(row[5]) if row[5] else None,
            )
            history.append((msg_in, msg_out))

        conn.close()
        return history
