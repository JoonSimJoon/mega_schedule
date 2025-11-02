FROM python:3.11-slim

# 환경 변수 설정 (Cloud Run에서 PORT 환경 변수를 사용하므로 동적으로 설정)
ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 시스템 의존성 설치 (불필요한 파일 제거하여 이미지 크기 최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 헬스 체크 (Cloud Run에서 자동으로 인스턴스 상태 모니터링)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health', timeout=5.0)"

# 애플리케이션 실행 (PORT 환경 변수 사용)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 2"]

