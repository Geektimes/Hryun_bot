from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# Создаем подключение к SQLite
DB_PATH = "chat_messages.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=True)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# Модель таблицы сообщений
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

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
