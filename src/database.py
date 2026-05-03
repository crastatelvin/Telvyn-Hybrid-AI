import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), index=True)
    role = Column(String(50))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database Setup
SQL_DB_URL = os.getenv("SQL_DB_URL", "sqlite:///./data/telvyn.db")
db_dir = os.path.dirname(SQL_DB_URL.replace("sqlite:///",""))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

engine = create_engine(SQL_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_message(session_id, role, content):
    db = SessionLocal()
    try:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()

def get_chat_history(session_id, limit=10):
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        return [{"role": m.role, "content": m.content} for m in reversed(messages)]
    finally:
        db.close()
