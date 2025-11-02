from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Enum
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
# Supabase PostgreSQL 또는 로컬 SQLite 선택
DATABASE_URL = os.getenv("DATABASE_URL")

# DATABASE_URL이 없거나 sqlite를 명시한 경우 SQLite 사용
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    DATABASE_URL = DATABASE_URL or "sqlite+aiosqlite:///./mega_schedule.db"
else:
    # Supabase PostgreSQL URL 형식 변환 (postgres:// -> postgresql+asyncpg://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# echo=True는 개발 환경에서만, 프로덕션에서는 False
echo = os.getenv("DB_ECHO", "False").lower() == "true"
engine = create_async_engine(DATABASE_URL, echo=echo)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    DESK = "desk"


class AssignmentStatus(str, enum.Enum):
    PENDING = "pending"  # 대기 중 (선생 수락 대기)
    ACCEPTED = "accepted"  # 수락됨
    REJECTED = "rejected"  # 거절됨


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # teacher or desk
    google_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)  # 수업 배정 가능 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    status = Column(String, default=AssignmentStatus.PENDING.value)
    created_by = Column(Integer, ForeignKey("users.id"))  # 데스크 유저 ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

