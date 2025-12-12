# utils\services.py
import logging
import random
import yaml
from aiogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from sqlalchemy.exc import SQLAlchemyError

from database import get_db, Message, User, Chat, UsedAnekdot
from config import load_config
from utils.redis_utils import get_user_from_redis, set_user_to_redis


config = load_config()
ANEKDOTS_FILE = config.ANEKDOTS_FILE


async def get_or_create_user(db: AsyncSession, tg_user_id: int, **kwargs):
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


async def get_message_props(message):
    props = {
        "tg_chat_id": message.chat.id,
        "tg_user_id": message.from_user.id,
        "tg_username": message.from_user.username or "",
        "tg_first_name": message.from_user.first_name,
        "tg_last_name": message.from_user.last_name or "",
        "tg_message_id": message.message_id,
        "message_content": (message.text if message.text else None),
        "reply_to_tg_message_id": message.reply_to_message.message_id if message.reply_to_message else None,
        "type": type,
    }
    props["chat_title"] =  message.chat.title if message.chat.title else f"Личный чат с {props.get('tg_first_name')}"

    return props


async def is_user_exists_or_create(message):
    try:
        async with get_db() as db:
            props = await get_message_props(message)

            # Проверяем наличие пользователя в Redis
            user_data = await get_user_from_redis(props["tg_user_id"])
            if user_data:
                return True, User(**user_data)

            # Если в Redis нет, проверяем в БД
            result = await db.execute(
                select(User).filter_by(tg_user_id=props["tg_user_id"])
            )
            user = result.scalar_one_or_none()
            if user:
                # Сохраняем пользователя в Redis
                user_data = {
                    "tg_username": user.tg_username,
                    "tg_first_name": user.tg_first_name,
                    "tg_last_name": user.tg_last_name,
                    "tg_user_id": user.tg_user_id,
                    "is_bot": user.is_bot
                }
                await set_user_to_redis(user.tg_user_id, user_data)
                return True, user
            else:
                # Создаем нового пользователя
                user = await get_or_create_user(
                    db,
                    props["tg_user_id"],
                    tg_username=props["tg_username"],
                    tg_first_name=props["tg_first_name"],
                    tg_last_name=props["tg_last_name"]
                )
                # Сохраняем нового пользователя в Redis
                user_data = {
                    "tg_username": user.tg_username,
                    "tg_first_name": user.tg_first_name,
                    "tg_last_name": user.tg_last_name,
                    "tg_user_id": user.tg_user_id,
                    "is_bot": user.is_bot
                }
                await set_user_to_redis(user.tg_user_id, user_data)
                return False, user

    except Exception as e:
        logging.error(f"Ошибка в состоянии юзера: {e}", exc_info=True)
        await db.rollback()


async def save_message(message, bot_addressed=False, type="None type"):
    try:
        async with get_db() as db:
            props = await get_message_props(message)
            # Получаем или создаем чат
            chat = await get_or_create_chat(db, props["tg_chat_id"], title=props["chat_title"])

            # Получаем или создаем пользователя
            user = await get_or_create_user(db, props["tg_user_id"], tg_username=props["tg_username"], tg_first_name=props["tg_first_name"],
                                            tg_last_name=props["tg_last_name"])

            # Если сообщение является реплаем, ищем его в БД
            reply_to_message = None
            if props["reply_to_tg_message_id"]:
                result = await db.execute(
                    select(Message).filter_by(tg_message_id=props["reply_to_tg_message_id"], chat_id=chat.id)
                )
                reply_to_message = result.scalar_one_or_none()

            # Сохраняем сообщение
            new_message = Message(
                tg_message_id=props['tg_message_id'],
                chat_id=chat.id,
                user_id=user.id,
                content=props["message_content"],
                bot_addressed=bot_addressed,
                type=type,
                reply_to_tg_message_id=reply_to_message.tg_message_id if reply_to_message else None
            )
            db.add(new_message)
            await db.commit()
            return new_message

    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения: {e}", exc_info=True)
        await db.rollback()


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



