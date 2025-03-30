# history_listing.py

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


def get_history_listing(tg_chat_id: int, limit: int = 100):
    messages = get_messages_with_users(tg_chat_id, limit)
    if messages:
        summary = []
        with SessionLocal() as session:
            for chat_message, user in messages:
                # Проверяем, является ли сообщение реплаем
                if chat_message.reply_to_tg_message_id:
                    # Ищем сообщение по tg_message_id и chat_id
                    replied_message = session.query(ChatMessage).filter_by(
                        tg_message_id=chat_message.reply_to_tg_message_id,
                        chat_id=chat_message.chat_id  # Учитываем чат
                    ).first()

                    if replied_message:
                        replied_user = session.get(User, replied_message.user_id)
                        replied_username = replied_user.username if replied_user else "Неизвестный"

                        summary.append(
                            f"{chat_message.timestamp} юзер '{user.username}' ответил на сообщение \"{replied_message.text}\" от юзера '{replied_username}' "
                            f" следующее: {chat_message.text}"
                        )
                    else:
                        print("⚠️ Ошибка: Не найдено сообщение, на которое идет ответ!")

                summary.append(
                    f"{chat_message.timestamp} юзер '{user.username}' сказал: {chat_message.text}")

        return "\n".join(summary)
    else:
        return "В этом чате пока нет сообщений для отчета."


if __name__ == "__main__":
    content = get_history_listing(tg_chat_id=-1002619036043, limit=4)
    print(content)
