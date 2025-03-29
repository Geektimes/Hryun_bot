# summary.py
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import SessionLocal, ChatMessage, Users


class Summary:
    def __init__(self, limit: int = 100):
        self.limit = limit

    def get_messages_with_users(self, chat_id: int):
        with SessionLocal() as session:
            stmt = (
                select(ChatMessage, Users)
                .join(Users, ChatMessage.user_id == Users.id)
                .where(ChatMessage.chat_id == chat_id)
                .order_by(ChatMessage.timestamp.desc())
                .limit(self.limit)
            )

            result = session.execute(stmt)
            return result.all()


if __name__ == "__main__":
    summary = Summary()
    messages = summary.get_messages_with_users(1)

    for chat_message, user in messages:
        print(f"{user.username} сказал: {chat_message.text}")