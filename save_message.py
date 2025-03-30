# save_message.py
from database import get_db, ChatMessage, User, Chat
from sqlalchemy.orm.exc import NoResultFound


async def save_message(tg_chat_id: int, chat_title: str, tg_user_id: int, username: str, text: str):
    db = next(get_db())
    try:
        # Проверяем, существует ли чат в БД
        chat = db.query(Chat).filter(Chat.tg_chat_id == tg_chat_id).first()
        if not chat:
            chat = Chat(
                tg_chat_id=tg_chat_id,
                title=chat_title  # Можно задать любое default название
            )
            db.add(chat)
            db.flush()

        # Проверяем, существует ли пользователь в БД
        user = db.query(User).filter(User.tg_user_id == tg_user_id).first()
        if not user:
            user = User(
                tg_user_id=tg_user_id,
                username=username
            )
            user.chats.append(chat)  # Добавляем чат в связь many-to-many

            db.add(user)
            db.flush()  # Чтобы получить ID нового пользователя

        # Создаем новое сообщение
        new_message = ChatMessage(
            chat_id=chat.id,  # Используем id из таблицы Chats
            user_id=user.id,  # Используем id из таблицы Users
            text=text
        )

        db.add(new_message)
        db.commit()

        return new_message

    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении сообщения: {e}")
        raise
    finally:
        db.close()
