from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./secureagent.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True)
    event_type = Column(String)
    tool = Column(String)
    reason = Column(String)
    risk = Column(Integer)
    goal = Column(String)


def init_db():
    Base.metadata.create_all(bind=engine)