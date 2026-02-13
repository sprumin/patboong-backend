# Django REST Framework 백엔드 프로젝트

## 기능
- JWT 인증 (로그인, 로그아웃, 토큰 갱신)
- 회원가입
- 게시판 CRUD
- 자동 로그아웃 (토큰 만료)

## 설치 및 실행

### 1. 가상환경 생성 및 활성화
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. 패키지 설치
```powershell
pip install -r requirements.txt
```

### 3. 환경변수 설정
```powershell
cp .env.example .env
```
.env 파일을 열어서 실제 값으로 수정하세요.

### 4. 데이터베이스 마이그레이션
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 5. 슈퍼유저 생성
```powershell
python manage.py createsuperuser
```

### 6. 서버 실행
```powershell
python manage.py runserver
```

## API 엔드포인트

### 인증 (Accounts)
- `POST /api/accounts/register/` - 회원가입
- `POST /api/accounts/login/` - 로그인
- `POST /api/accounts/logout/` - 로그아웃
- `GET /api/accounts/profile/` - 프로필 조회
- `POST /api/accounts/token/refresh/` - 토큰 갱신

### 게시판 (Boards)
- `GET /api/boards/` - 게시글 목록
- `POST /api/boards/` - 게시글 작성
- `GET /api/boards/{id}/` - 게시글 상세
- `PUT /api/boards/{id}/` - 게시글 수정
- `DELETE /api/boards/{id}/` - 게시글 삭제

## 인증 헤더
```
Authorization: Bearer {access_token}
```

## JWT 토큰 설정
- Access Token: 1시간
- Refresh Token: 7일
- 자동 로그아웃: Access Token 만료 시

## Docker 배포

### 1. 환경변수 파일 생성
```powershell
cp .env.example .env
```
`.env` 파일을 열어서 실제 값으로 수정하세요.

### 2. MySQL과 함께 배포
```powershell
docker-compose up -d
```

### 배포 스크립트 실행
```powershell
.\deploy.ps1
```

### 유용한 Docker 명령어
```powershell
docker-compose logs -f backend
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py migrate
docker-compose down
docker-compose down -v
```

## 환경변수 설정

`.env` 파일을 프로젝트 루트에 생성하세요 (`.env.example` 참고)

주요 환경변수:
- `SECRET_KEY` - Django 시크릿 키 (필수 변경)
- `DEBUG` - 디버그 모드 (프로덕션: False)
- `ALLOWED_HOSTS` - 허용 호스트 (쉼표 구분)
- `DATABASE_ENGINE` - django.db.backends.mysql (고정)
- `DATABASE_NAME` - DB 이름
- `DATABASE_USER` - DB 사용자
- `DATABASE_PASSWORD` - DB 비밀번호
- `DATABASE_HOST` - DB 호스트 (Docker: db, 외부: IP/도메인)
- `DATABASE_PORT` - DB 포트 (기본: 3306)
- `CORS_ALLOWED_ORIGINS` - CORS 허용 도메인 (쉼표 구분)
