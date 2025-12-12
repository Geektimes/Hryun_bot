# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from contextlib import asynccontextmanager

from config import load_config

config = load_config()

# Создаем подключение к SQLite
file_path = config.DB_PATH
DATABASE_URL = f"sqlite+aiosqlite:///{file_path}"

# Создаем таблицы в базе данных
async def init_db():
    if not os.path.exists(file_path):
        print(f"База данных {file_path} не найдена. Создаем новую...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("База данных успешно создана.")
    else:
        print(f"База данных {file_path} уже существует.")


# Асинхронный контекстный менеджер для сессий
@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

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
    content = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    reply_to_tg_message_id = Column(Integer, ForeignKey("messages.tg_message_id"), nullable=True)
    bot_addressed = Column(Boolean, default=False, nullable=False)
    type = Column(String, nullable=False)

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


class UsedAnekdot(Base):
    __tablename__ = "used_anekdots"
    anekdot_key = Column(String, primary_key=True, index=True)

