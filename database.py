# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime


# Создаем подключение к SQLite
DB_PATH = "db.sqlite3"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# Промежуточная таблица для связи многие-ко-многим между пользователями и чатами
user_chat_association = Table(
    "user_chat_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("chat_id", Integer, ForeignKey("chats.id"), primary_key=True),
)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_message_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reply_to_tg_message_id = Column(Integer, ForeignKey("messages.tg_message_id"), nullable=True)
    bot_addressed = Column(Boolean, default=False, nullable=False)

    # Связи
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")
    reply_to_message = relationship("Message", remote_side=[tg_message_id], backref="replies")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_username = Column(String, nullable=True)
    tg_first_name = Column(String, nullable=False)
    tg_last_name = Column(String, nullable=True)
    tg_user_id = Column(Integer, nullable=True)
    is_bot = Column(Boolean, default=False, nullable=False)

    # Связи
    chats = relationship("Chat", secondary=user_chat_association, back_populates="users")
    messages = relationship("Message", back_populates="user")


# Модель чатов
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_chat_id = Column(Integer, nullable=True)
    title = Column(String, nullable=True)

    # Связи
    users = relationship("User", secondary=user_chat_association, back_populates="chats")
    messages = relationship("Message", back_populates="chat")


# Создаем таблицы в базе данных
def init_db():
    if not os.path.exists(DB_PATH):
        print(f"База данных {DB_PATH} не найдена. Создаем новую...")
        Base.metadata.create_all(engine)
        print("База данных успешно создана.")
    else:
        print(f"База данных {DB_PATH} уже существует.")


# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
