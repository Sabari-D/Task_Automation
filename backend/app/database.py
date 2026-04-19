from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, String, Text, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://aw_user:aw_password@localhost:5432/aw_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
if DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Sync URL for use inside background threads
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

# Async engine (for FastAPI endpoints)
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine (for background threads)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine)

Base = declarative_base()

class TaskRecord(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String, default="pending")
    result = Column(Text, nullable=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def sync_update_task(task_id: str, status: str, result: str = None):
    """Thread-safe synchronous DB update for background workers."""
    with SyncSessionLocal() as session:
        task = session.get(TaskRecord, task_id)
        if task:
            task.status = status
            if result is not None:
                task.result = result
            session.commit()
