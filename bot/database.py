from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import pytz

from bot.config import Config

Base = declarative_base()

# Создаем engine для PostgreSQL
engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    is_active = Column(Boolean, default=True)
    learning_mode = Column(Boolean, default=True)
    learning_end_time = Column(DateTime)
    personality_level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC))
    
    messages = relationship("Message", back_populates="chat")
    patterns = relationship("Pattern", back_populates="chat")
    statistics = relationship("Statistic", back_populates="chat")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    message_count = Column(Integer, default=0)
    style_patterns = Column(Text)  # JSON
    last_seen = Column(DateTime, default=datetime.now(pytz.UTC))
    created_at = Column(DateTime, default=datetime.now(pytz.UTC))
    
    messages = relationship("Message", back_populates="user")
    patterns = relationship("Pattern", back_populates="user")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    message_id = Column(Integer)
    text = Column(Text)
    message_type = Column(String)  # text, sticker, photo, etc.
    timestamp = Column(DateTime, default=datetime.now(pytz.UTC))
    is_processed = Column(Boolean, default=False)
    has_reaction = Column(Boolean, default=False)
    
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User", back_populates="messages")

class Pattern(Base):
    __tablename__ = 'patterns'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    pattern_text = Column(Text, nullable=False)
    pattern_type = Column(String)  # word, phrase, sticker, joke, topic
    frequency = Column(Integer, default=1)
    context = Column(Text)  # JSON контекста
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC))
    
    chat = relationship("Chat", back_populates="patterns")
    user = relationship("User", back_populates="patterns")

class Statistic(Base):
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    date = Column(DateTime, default=datetime.now(pytz.UTC))
    total_messages = Column(Integer, default=0)
    bot_responses = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    personality_level = Column(Integer, default=1)
    
    chat = relationship("Chat", back_populates="statistics")

class Reaction(Base):
    __tablename__ = 'reactions'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'))
    reaction_type = Column(String)  # like, dislike, funny, etc.
    user_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now(pytz.UTC))

class Quote(Base):
    __tablename__ = 'quotes'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'))
    week_number = Column(Integer)
    year = Column(Integer)
    votes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now(pytz.UTC))

# Создание таблиц
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()