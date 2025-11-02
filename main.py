from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from database import init_db, get_db, User
from auth import get_current_user
from routers import teacher, desk
from models import UserResponse
import os
import re
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 데이터베이스 초기화
    await init_db()
    yield
    # 종료 시 정리 작업 (필요시)

app = FastAPI(
    title="Mega Schedule API",
    description="선생-학원 관리 시스템 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 - 프론트엔드에서 접근 가능하도록
# 환경 변수에서 프론트엔드 URL을 가져오거나 기본값 사용
# 공백 또는 쉼표로 분리
frontend_urls_str = os.getenv("FRONTEND_URLS", "")
frontend_urls = re.split(r'[,\s]+', frontend_urls_str)
frontend_urls = [url.strip() for url in frontend_urls if url.strip()]

default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]

# 환경 변수에 값이 있으면 추가
if frontend_urls:
    default_origins.extend(frontend_urls)

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(teacher.router)
app.include_router(desk.router)


@app.get("/")
async def root():
    return {
        "message": "Mega Schedule API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/api/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 유저 정보 조회"""
    return current_user


@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}

