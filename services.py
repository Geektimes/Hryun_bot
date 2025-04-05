# services.py
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from database import SessionLocal, get_db, Message, User, Chat
import logging
import yaml
import random


def get_two_users_conversation(
        first_tg_user_id: int,
        second_tg_user_id: int,
        chat_id: int, limit: int
):
    session = SessionLocal()
    try:
        # Запрашиваем сообщения, где пользователь или адресовал бота, или это ответное сообщение
        messages = (
            session.query(Message)
            .join(User, Message.user_id == User.id)
            .filter(
                Message.chat_id == chat_id,
                or_(User.tg_user_id == first_tg_user_id, User.tg_user_id == second_tg_user_id),
            )
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .options(
                joinedload(Message.user),  # Подгружаем данные пользователя
                joinedload(Message.reply_to_message)  # Подгружаем связанные сообщения (реплаи)
            )
            .all()
        )
        messages.reverse()
        return messages
    finally:
        session.close()


async def save_message(
        tg_chat_id: int,
        chat_title: str,
        tg_user_id: int,
        tg_username: str,
        tg_first_name: str,
        tg_last_name: str,
        content: str,
        tg_message_id: int,
        bot_addressed: bool=False,
        reply_to_tg_message_id: int=None
):
    db = next(get_db())
    try:
        # Получаем или создаем чат
        chat = db.query(Chat).filter_by(tg_chat_id=tg_chat_id).first()
        if not chat:
            chat = Chat(tg_chat_id=tg_chat_id, title=chat_title)
            db.add(chat)
            db.commit()

        # Получаем или создаем пользователя
        user = db.query(User).filter_by(tg_user_id=tg_user_id).first()
        if not user:
            user = User(
                tg_user_id=tg_user_id,
                tg_username=tg_username,
                tg_first_name=tg_first_name,
                tg_last_name=tg_last_name
            )
            db.add(user)
            db.commit()

        # Если сообщение является реплаем, ищем его в БД
        reply_to_message = None
        if reply_to_tg_message_id:
            reply_to_message = db.query(Message).filter_by(
                tg_message_id=reply_to_tg_message_id, chat_id=chat.id
            ).first()

        # Сохраняем сообщение
        message = Message(
            tg_message_id=tg_message_id,
            chat_id=chat.id,
            user_id=user.id,
            content=content,
            bot_addressed=bot_addressed,
            reply_to_tg_message_id=reply_to_message.tg_message_id if reply_to_message else None
        )
        db.add(message)
        db.commit()

    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения: {e}", exc_info=True)
        db.rollback()  # Откат изменений при ошибке

    finally:
        db.close()


async def get_anekdot():
    with open("anekdots.yaml", "r", encoding="utf-8") as f:
        anekdots = yaml.safe_load(f)
        random_key = random.choice(list(anekdots.keys()))
        return f"Ане́кдот №{random_key}:\n\n{anekdots[random_key]}"


if __name__ == "__main__":
    conversation = get_two_users_conversation(first_tg_user_id=1585006634, second_tg_user_id=0, chat_id=1, limit=10)
    print("TYPE ", type(conversation), "\n\n")
    for msg in conversation:
        reply_info = f" (в ответ на {msg.reply_to_message.content})" if msg.reply_to_message else ""
        print(f"{msg.timestamp} | {msg.user.username}: {msg.content}{reply_info}")
