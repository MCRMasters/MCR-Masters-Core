# MCR-Masters-Core
Backend API server for MCR-Masters

## 개발 환경 준비

### 사전 준비사항
[프로젝트 설치 가이드](https://github.com/MCRMasters/MCR-Masters-Hub)

필수 항목:
- Python 3.12.9
- Poetry
- Docker & Docker Compose
- PostgreSQL

## 프로젝트 설정

### 1. 저장소 클론
```bash
git clone https://github.com/MCRMasters/MCR-Masters-Core.git
cd MCR-Masters-Core
```

### 2. 의존성 설치
```bash
poetry install
```

### 3. 환경 변수 설정
`.env.sample` 파일을 복사하여 `.env` 파일을 생성합니다:

```bash
cp .env.sample .env
```

그런 다음 `.env` 파일을 열고 필요한 값들을 수정합니다. 특히 다음 항목들을 본인의 환경에 맞게 설정해주세요:
- 데이터베이스 연결 정보 (`POSTGRES_` 관련 설정)
- JWT 시크릿 키 (`JWT_SECRET_KEY`)
- Google OAuth 클라이언트 정보 (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`)

테스트 환경을 위해서도 `.env.test` 파일을 생성합니다:

```bash
cp .env.sample .env.test
```

`.env.test` 파일을 열고 테스트 환경에 맞는 값으로 수정합니다. 특히 `ENVIRONMENT=test`로 설정하고, 테스트용 데이터베이스 정보를 설정해야 합니다.

### 4. 데이터베이스 컨테이너 실행
```bash
docker-compose up -d
```

### 5. 데이터베이스 마이그레이션
```bash
poetry run init-db     # 데이터베이스 초기화
poetry run migrate     # 마이그레이션 적용
```

### 6. pre-commit 훅 설치
```bash
poetry run pre-commit install
```

### 7. 테스트 실행
```bash
poetry run pytest
```

### 8. 애플리케이션 실행
```bash
# 개발 모드 실행 (자동 리로드)
poetry run start

# 프로덕션 모드 실행
poetry run start-prod
```
