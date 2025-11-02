# Mega Schedule - 선생-학원 관리 시스템

## 프로젝트 개요
선생과 학원 데스크를 위한 스케줄 및 수업 관리 시스템입니다.

## 기능
### 선생 (Teacher)
- 본인 일정 등록
- 배정된 수업 확인
- 이번달 근무시간 확인 (정산)
- 대기 중 수업 수락

### 학원 데스크 (Desk)
- 학생 배정 (선생 가능 시간 조회)
- 선생들 근무 일정 및 시간 조회

## 기술 스택
- Backend: FastAPI
- Database: SQLite (개발) / Supabase PostgreSQL (운영)
- Authentication: Google OAuth
- 배포: Railway / Render / Fly.io / Docker

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:
```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret  # 참고용 (실제 사용은 Google Client ID만 필요)
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite+aiosqlite:///./mega_schedule.db
FRONTEND_URLS=https://your-frontend-url.web.app,https://your-frontend-url.firebaseapp.com
```

**Google OAuth 설정:**
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. OAuth 2.0 클라이언트 ID 생성
3. 승인된 JavaScript 원본에 프론트엔드 URL 추가
4. 승인된 리디렉션 URI에 백엔드 URL 추가 (필요시)
5. 생성된 Client ID를 `GOOGLE_CLIENT_ID`에 설정

### 3. 서버 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서
서버 실행 후 `http://localhost:8000/docs` 에서 API 문서를 확인할 수 있습니다.

## 배포

### 🏗️ 최종 아키텍처
```
프론트엔드 (Firebase Hosting) 
    ↓ (API 호출)
백엔드 (Google Cloud Run)
    ↓ (쿼리)
데이터베이스 (Supabase PostgreSQL)
```

### 배포 플랫폼
- **백엔드**: Google Cloud Run (월 200만 요청 무료) ✅
- **프론트엔드**: Firebase Hosting (무료) ✅
- **데이터베이스**: Supabase PostgreSQL (월 500MB 무료) ✅

### 배포 가이드
자세한 배포 가이드는 [CLOUD_RUN_DEPLOYMENT.md](./CLOUD_RUN_DEPLOYMENT.md)를 참조하세요.

