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

class ToolUsage(Base):
    __tablename__ = 'tool_usage'
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255))
    tool_name = Column(String(255))
    input_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TokenUsage(Base):
    __tablename__ = 'token_usage'
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
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

def log_tool_usage(session_id, tool_name, input_data):
    db = SessionLocal()
    try:
        usage = ToolUsage(
            session_id=session_id, 
            tool_name=tool_name, 
            input_data=str(input_data)
        )
        db.add(usage)
        db.commit()
    except Exception as e:
        print(f"Error logging tool usage: {e}")
    finally:
        db.close()

def log_token_usage(session_id, prompt_tokens, completion_tokens):
    db = SessionLocal()
    try:
        usage = TokenUsage(
            session_id=session_id, 
            prompt_tokens=prompt_tokens, 
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        db.add(usage)
        db.commit()
    except Exception as e:
        print(f"Error logging token usage: {e}")
    finally:
        db.close()

def get_total_tokens(session_id):
    db = SessionLocal()
    try:
        from sqlalchemy import func
        result = db.query(func.sum(TokenUsage.total_tokens)).filter(
            TokenUsage.session_id == session_id
        ).scalar()
        return result or 0
    finally:
        db.close()

def get_all_sessions():
    db = SessionLocal()
    try:
        from sqlalchemy import func
        # Get unique session IDs and their latest message timestamp
        sessions = db.query(
            ChatMessage.session_id, 
            func.max(ChatMessage.timestamp).label('last_active')
        ).group_by(ChatMessage.session_id).order_by(func.max(ChatMessage.timestamp).desc()).all()
        return [{"id": s.session_id, "last_active": s.last_active.isoformat()} for s in sessions]
    finally:
        db.close()
