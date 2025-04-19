# utils\services.py
import logging
import random
import yaml
import os
import asyncio
import time
from functools import wraps
from aiogram.types import Message
# from aiogram.exceptions import Throttled

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


async def get_or_create_user(db: AsyncSession, tg_user_id: int, **kwargs):
    async with db.begin():
        result = await db.execute(
            select(User).filter_by(tg_user_id=tg_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(tg_user_id=tg_user_id, **kwargs)
            db.add(user)
            await db.commit()
        return user


async def get_or_create_chat(db: AsyncSession, tg_chat_id: int, title=None):
    async with db.begin():
        result = await db.execute(
            select(Chat).filter_by(tg_chat_id=tg_chat_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            chat = Chat(tg_chat_id=tg_chat_id, title=title)
            db.add(chat)
            await db.commit()
        return chat


async def save_message(message, bot_addressed=False, type="None type"):
    tg_chat_id = message.chat.id
    tg_user_id = message.from_user.id
    tg_username = message.from_user.username or ""
    tg_first_name = message.from_user.first_name  # Имя пользователя
    tg_last_name = message.from_user.last_name or ""  # Фамилия (может быть пустой)
    chat_title = message.chat.title if message.chat.title else f"Личный чат с {tg_first_name}"
    tg_message_id = message.message_id
    message_content = message.text if message.text else None
    type = type
    reply_to_tg_message_id = message.reply_to_message.message_id if message.reply_to_message else None

    try:
        async with get_db() as db:
            # Получаем или создаем чат
            chat = await get_or_create_chat(db, tg_chat_id, title=chat_title)

            # Получаем или создаем пользователя
            user = await get_or_create_user(db, tg_user_id, tg_username=tg_username, tg_first_name=tg_first_name,
                                            tg_last_name=tg_last_name)

            # Если сообщение является реплаем, ищем его в БД
            reply_to_message = None
            if reply_to_tg_message_id:
                result = await db.execute(
                    select(Message).filter_by(tg_message_id=reply_to_tg_message_id, chat_id=chat.id)
                )
                reply_to_message = result.scalar_one_or_none()

            # Сохраняем сообщение
            new_message = Message(
                tg_message_id=tg_message_id,
                chat_id=chat.id,
                user_id=user.id,
                content=message_content,
                bot_addressed=bot_addressed,
                type=type,
                reply_to_tg_message_id=reply_to_message.tg_message_id if reply_to_message else None
            )
            db.add(new_message)
            await db.commit()

    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения: {e}", exc_info=True)
        await db.rollback()  # Откат изменений при ошибке


async def get_anekdot():
    # Загружаем анекдоты из файла
    with open(ANEKDOTS_FILE, "r", encoding="utf-8") as f:
        anekdots = yaml.safe_load(f)
    all_keys = list(anekdots.keys())

    async with get_db() as db:
        try:
            # Получаем использованные ключи из таблицы UsedAnekdot
            result = await db.execute(select(UsedAnekdot.anekdot_key))
            used_keys = [row[0] for row in result.fetchall()]

            # Если все анекдоты использованы — очищаем таблицу
            if len(used_keys) >= len(all_keys):
                await db.execute(delete(UsedAnekdot))
                await db.commit()
                used_keys = []

            # Находим доступные ключи и выбираем случайный
            available_keys = list(set(all_keys) - set(used_keys))
            if not available_keys:
                raise ValueError("Нет доступных анекдотов")

            random_key = random.choice(available_keys)

            # Добавляем использованный ключ в таблицу
            stmt = insert(UsedAnekdot).values(anekdot_key=random_key)
            await db.execute(stmt)
            await db.commit()

            return f"Ане́кдот №{random_key}:\n\n{anekdots[random_key]}"

        except SQLAlchemyError as e:
            logging.error(f"Ошибка при работе с базой данных: {e}", exc_info=True)
            await db.rollback()
        except Exception as e:
            logging.error(f"Ошибка при получении анекдота: {e}", exc_info=True)



