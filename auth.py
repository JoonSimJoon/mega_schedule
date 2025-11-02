from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, User, UserRole
from google.auth.transport import requests
from google.oauth2 import id_token
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()


async def verify_google_token(token: str) -> dict:
    """Google ID 토큰 검증"""
    try:
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GOOGLE_CLIENT_ID not configured"
            )
        
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return idinfo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """현재 인증된 유저 가져오기"""
    token = credentials.credentials
    google_info = await verify_google_token(token)
    
    email = google_info.get('email')
    google_id = google_info.get('sub')
    name = google_info.get('name', email)
    
    # 유저 조회 또는 생성
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # 새 유저 생성 (기본 역할은 teacher)
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            role=UserRole.TEACHER.value
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.google_id:
        # google_id 업데이트
        user.google_id = google_id
        await db.commit()
        await db.refresh(user)
    
    return user


async def require_role(required_role: UserRole, current_user: User = Depends(get_current_user)) -> User:
    """특정 역할이 필요한 엔드포인트용 의존성"""
    if current_user.role != required_role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {required_role.value}"
        )
    return current_user


async def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    """선생 역할 체크"""
    return await require_role(UserRole.TEACHER, current_user)


async def require_desk(current_user: User = Depends(get_current_user)) -> User:
    """데스크 역할 체크"""
    return await require_role(UserRole.DESK, current_user)

