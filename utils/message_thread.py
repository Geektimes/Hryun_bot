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


async def get_message_thread(db: AsyncSession, tg_user_id: int, tg_chat_id: int, limit: int=20, **kwargs):
    """ Строит цепочку сообщений в заданном чате между юзером и ботом по реплаям и по признаку bot_addressed=True
        (значит сообщение адресовано или принадлежит боту).
        Возвращает словарь для создания контекста для OpenAI.
    """
    async with (db.begin()):
        # Находим пользователя и чат
        user_result = await db.execute(
            select(User).filter_by(tg_user_id=tg_user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []
            # return {"error": "Пользователь не найден"}

        chat_result = await db.execute(
            select(Chat).filter_by(tg_chat_id=tg_chat_id)
        )
        chat = chat_result.scalar_one_or_none()
        if not chat:
            # return {"error": "Чат не найден"}
            return []

        # Получаем все сообщения в чате с bot_addressed=True, связанные с пользователем или ботом
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
            # return {"messages": [], "context": "Нет сообщений в цепочке"}
            return []

        # Строим цепочку сообщений на основе reply_to_tg_message_id
        message_dict = {msg.tg_message_id: (msg, usr) for msg, usr in messages}
        thread = []
        seen_messages = set()

        def build_thread(current_msg_id):
            if current_msg_id in seen_messages:
                return  # Предотвращаем зацикливание
            if current_msg_id not in message_dict:
                return  # Сообщение не найдено или не входит в bot_addressed

            msg, usr = message_dict[current_msg_id]
            seen_messages.add(current_msg_id)
            thread_entry = {
                "user": usr.tg_username or usr.tg_first_name,
                "content": msg.content or f"[{msg.type}]"
            }

            # Если есть сообщение, на которое это ответ
            if msg.reply_to_tg_message_id:
                build_thread(msg.reply_to_tg_message_id)
                thread.append(thread_entry)
            else:
                thread.append(thread_entry)

        # Начинаем с последнего сообщения пользователя, если указано конкретное сообщение
        start_message_id = kwargs.get("start_tg_message_id")
        if start_message_id and start_message_id in message_dict:
            build_thread(start_message_id)
        else:
            # Иначе берем все сообщения и строим полную цепочку
            for msg_id in message_dict:
                if msg_id not in seen_messages:
                    build_thread(msg_id)

        # Формируем текстовый контекст для OpenAI
        context = []
        for entry in thread:
            strip = {}
            role = "assistant" if entry["user"] == "hryun2_bot" else "user"
            strip["role"] = role
            strip["content"] = entry['content']
            context.append(strip)
        return context[-limit:]


# Тестовая функция для запуска get_message_thread
async def main():
    async with get_db() as db:
        thread = await get_message_thread(db=db, tg_user_id=1585006634, tg_chat_id=-1002619036043, limit=5)

        print("Результат get_message_thread:")
        for i in thread:
            print(i)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())