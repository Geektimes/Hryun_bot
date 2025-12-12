# utils\message_thread.py
import logging
import random
import yaml
import os
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from sqlalchemy import select, insert, delete, exists
from sqlalchemy.exc import SQLAlchemyError

from database import get_db, Message, User, Chat, UsedAnekdot
from config import load_config

config = load_config()
ANEKDOTS_FILE = config.ANEKDOTS_FILE


async def get_message_thread(db: AsyncSession, tg_user_id: int, tg_chat_id: int, limit: int = 20, **kwargs):
    """
    Строит цепочку сообщений между юзером и ботом.
    Возвращает список сообщений в формате Gemini:
        {
            "role": "user" / "assistant",
            "parts": [{"text": "..."}]
        }
    """
    async with db.begin():
        # Находим пользователя
        user_result = await db.execute(
            select(User).filter_by(tg_user_id=tg_user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []

        # Находим чат
        chat_result = await db.execute(
            select(Chat).filter_by(tg_chat_id=tg_chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            return []

        # Все bot_addressed сообщения
        stmt = (
            select(Message, User)
            .join(User, Message.user_id == User.id)
            .where(
                Message.chat_id == chat.id,
                Message.bot_addressed == True
            )
            .order_by(Message.timestamp.asc())
        )
        result = await db.execute(stmt)
        messages = result.all()

        if not messages:
            return []

        # Собираем сообщения в словарь
        message_dict = {msg.tg_message_id: (msg, usr) for msg, usr in messages}
        thread = []
        seen_messages = set()

        def build_thread(current_msg_id):
            """Рекурсивное построение цепочки reply_to"""
            if current_msg_id in seen_messages:
                return
            if current_msg_id not in message_dict:
                return

            msg, usr = message_dict[current_msg_id]
            seen_messages.add(current_msg_id)

            entry = {
                "user": usr.tg_username or usr.tg_first_name,
                "content": msg.content or f"[{msg.type}]"
            }

            # Если это ответ — сначала родитель
            if msg.reply_to_tg_message_id:
                build_thread(msg.reply_to_tg_message_id)

            thread.append(entry)

        # Если задано конкретное сообщение — цепочка вокруг него
        start_message_id = kwargs.get("start_tg_message_id")
        if start_message_id and start_message_id in message_dict:
            build_thread(start_message_id)
        else:
            # Иначе строим цепочку по всем сообщениям
            for msg_id in message_dict:
                if msg_id not in seen_messages:
                    build_thread(msg_id)

        # --------------------------------------------------------------------
        # ✔ Конвертация в формат Gemini (исправление ОШИБКИ)
        # --------------------------------------------------------------------
        context = []
        for entry in thread:
            role = "assistant" if entry["user"] == "hryun2_bot" else "user"

            context.append({
                "role": role,
                "parts": [
                    {"text": entry["content"]}
                ]
            })

        return context[-limit:]


# ТЕСТ
async def main():
    async with get_db() as db:
        thread = await get_message_thread(
            db=db,
            tg_user_id=1585006634,
            tg_chat_id=-1002619036043,
            limit=5
        )

        print("Результат get_message_thread:")
        for i in thread:
            print(i)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
