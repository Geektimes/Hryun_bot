# summary.py

from sqlalchemy import select
from database import SessionLocal, ChatMessage, User


def get_messages_with_users(tg_chat_id: int, limit: int):
    with SessionLocal() as session:
        stmt = (
            select(ChatMessage, User)
            .join(User, ChatMessage.user_id == User.id)
            .join(ChatMessage.chat)  # Добавляем связь с чатом
            .where(ChatMessage.chat.has(tg_chat_id=tg_chat_id))  # Фильтр по Telegram ID чата
            .order_by(ChatMessage.timestamp.desc())
            .limit(limit)
        )

        result = session.execute(stmt)
        return result.all()


def get_summary(tg_chat_id: int, limit: int = 100):
    messages = get_messages_with_users(tg_chat_id, limit)
    if messages:
        summary = "\n".join(
            f"{chat_message.timestamp} юзер '{user.username}' сказал: {chat_message.text}"
            for chat_message, user in messages
        )
    else:
        summary = "В этом чате пока нет сообщений для отчета."

    return summary


if __name__ == "__main__":
    content = get_summary(tg_chat_id=-1002619036043)
    print(content)
