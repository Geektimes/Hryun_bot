# save_message.py
from database import get_db, ChatMessage, User, Chat
import logging


async def save_message(tg_chat_id: int, chat_title: str, tg_user_id: int, username: str, text: str, tg_message_id: int, reply_to_tg_message_id: int=None):
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
            user = User(tg_user_id=tg_user_id, username=username)
            db.add(user)
            db.commit()

        # Если сообщение является реплаем, ищем его в БД
        reply_to_message = None
        if reply_to_tg_message_id:
            reply_to_message = db.query(ChatMessage).filter_by(
                tg_message_id=reply_to_tg_message_id, chat_id=chat.id
            ).first()

        # Сохраняем сообщение
        message = ChatMessage(
            tg_message_id=tg_message_id,
            chat_id=chat.id,
            user_id=user.id,
            text=text,
            reply_to_tg_message_id=reply_to_message.tg_message_id if reply_to_message else None
        )
        db.add(message)
        db.commit()

    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения: {e}")
        db.rollback()  # Откат изменений при ошибке

    finally:
        db.close()
