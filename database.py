# database.py

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Создаем подключение к SQLite
DB_PATH = "chat_messages.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


# Модель таблицы сообщений
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Связи
    chat = relationship("Chats", back_populates="messages")
    user = relationship("Users", back_populates="messages")


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True)
    tg_user_id = Column(Integer, nullable=True)
    chats_id = Column(Integer, ForeignKey('chats.id'), nullable=False)

    # Связи
    chats = relationship("Chats", back_populates="user")
    messages = relationship("ChatMessage", back_populates="user")


class Chats(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_chat_id = Column(Integer, nullable=True)
    title = Column(String, nullable=True)

    # Связи
    user = relationship("Users", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat")

# Создаем таблицы в базе данных
def init_db():
    Base.metadata.create_all(engine)

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
