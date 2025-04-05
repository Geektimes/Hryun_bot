# history_listing.py

from sqlalchemy import select
from database import SessionLocal, Message, User


def get_messages_with_users(tg_chat_id: int, limit: int):
    with SessionLocal() as session:
        stmt = (
            select(Message, User)
            .join(User, Message.user_id == User.id)
            .join(Message.chat)  # Добавляем связь с чатом
            .where(Message.chat.has(tg_chat_id=tg_chat_id))  # Фильтр по Telegram ID чата
            .order_by(Message.timestamp.desc())
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
                    replied_message = session.query(Message).filter_by(
                        tg_message_id=chat_message.reply_to_tg_message_id,
                        chat_id=chat_message.chat_id  # Учитываем чат
                    ).first()

                    if replied_message:
                        replied_user = session.get(User, replied_message.user_id)
                        replied_username = replied_user.username if replied_user else "Неизвестный"
                        short_text = replied_message.content[:80] + "..." if len(
                            replied_message.content) > 80 else replied_message.content

                        summary.append(
                            f"{chat_message.timestamp} юзер '{user.username}' ответил \"{chat_message.content}\" на сообщение \"{short_text}\" от юзера '{replied_username}'"
                        )
                    else:
                        print("⚠️ Ошибка: Не найдено сообщение, на которое идет ответ!")

                else:
                    summary.append(
                    f"{chat_message.timestamp} юзер '{user.username}' сказал: {chat_message.content}")
        summary.reverse()
        return "\n".join(summary)
    else:
        return "В этом чате пока нет сообщений для отчета."


if __name__ == "__main__":
    content = get_history_listing(tg_chat_id=-1002619036043, limit=4)
    print(content)
