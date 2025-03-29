from sqlalchemy.orm import Session
from database import ChatMessage, get_db

async def save_message(chat_id: int, user_id: int, username: str, text: str):
    db = next(get_db())
    try:
        new_message = ChatMessage(
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            text=text
        )
        db.add(new_message)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении сообщения: {e}")
    finally:
        db.close()
