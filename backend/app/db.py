from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# SQLite database file
DATABASE_URL = "sqlite:///./secureagent.db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Base class for models
Base = declarative_base()


# Security events table
class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    event_type = Column(String)   # TOOL_OK, TOOL_BLOCKED, PROMPT_BLOCKED
    tool = Column(String)
    reason = Column(String)
    risk = Column(Integer)
    goal = Column(String)


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)