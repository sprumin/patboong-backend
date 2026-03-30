# Django REST Framework 백엔드 프로젝트

## 기능
- JWT 인증 (로그인, 로그아웃, 토큰 갱신)
- 회원가입
- 게시판 CRUD
- 자동 로그아웃 (토큰 만료)

## 설치 및 실행

### Docker로 실행 (권장)

#### 1. 환경변수 설정
```bash
# Django 설정
cp .env.example .env

# MySQL 설정
cp .db.env.example .db.env
```
각 파일을 열어서 실제 값으로 수정하세요.

#### 2. Docker Compose로 실행
```bash
docker-compose up -d
```

#### 3. 마이그레이션 확인
마이그레이션 파일이 이미 포함되어 있으므로 자동으로 실행됩니다.

#### 4. 슈퍼유저 생성
```bash
docker exec -it backend python manage.py createsuperuser
```

#### 5. 접속
- API: http://localhost:8000/api/boards/
- Admin: http://localhost:8000/admin/

---

### 로컬 개발 환경

#### 1. 가상환경 생성 및 활성화
```powershell
python -m venv venv
.\venv\Scripts\activate
```

#### 2. 패키지 설치
```powershell
pip install -r requirements.txt
```

#### 3. 환경변수 설정
```powershell
cp .env.example .env
```
.env 파일을 열어서 실제 값으로 수정하세요.

#### 4. 데이터베이스 마이그레이션
```powershell
python manage.py migrate
```

#### 5. 슈퍼유저 생성
```powershell
python manage.py createsuperuser
```

#### 6. 서버 실행
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

## API 상세 설명

### 회원가입 (POST /api/accounts/register/)

**요청 예시:**
```json
{
  "userId": "hong123",
  "userPw": "password123!@",
  "mainLine": "mid",
  "subLine": "top",
  "tierTop": "gold",
  "tierJungle": "silver",
  "tierMid": "platinum",
  "tierAdc": "bronze",
  "tierSupport": "iron",
  "question": "pet",
  "answer": "멍멍이",
  "serviceTerms": true,
  "privacyTerms": true,
  "ageTerms": true,
  "marketingTerms": false,
  "eventTerms": false
}
```

**필드 설명:**
- `userId` (string, 필수): 로그인 아이디 (중복 불가)
- `userPw` (string, 필수): 비밀번호 (서버에서 bcrypt로 암호화 저장)
- `mainLine` (string, 선택): 주 라인 (top, jungle, mid, adc, support)
- `subLine` (string, 선택): 부 라인 (top, jungle, mid, adc, support)
- `tierTop` (string, 선택): 탑 티어 (iron, bronze, silver, gold, platinum, diamond, master, grandmaster, challenger)
- `tierJungle` (string, 선택): 정글 티어
- `tierMid` (string, 선택): 미드 티어
- `tierAdc` (string, 선택): 원딜 티어
- `tierSupport` (string, 선택): 서포트 티어
- `question` (string, 필수): 비밀번호 찾기 질문 (pet, school, food, city, friend)
- `answer` (string, 필수): 비밀번호 찾기 답변
- `serviceTerms` (boolean, 필수): 서비스 이용약관 동의
- `privacyTerms` (boolean, 필수): 개인정보 수집 동의
- `ageTerms` (boolean, 필수): 만 14세 이상 확인
- `marketingTerms` (boolean, 선택): 마케팅 수신 동의
- `eventTerms` (boolean, 선택): 이벤트 알림 동의

**응답 예시 (성공):**
```json
{
  "id": 1,
  "username": "hong123",
  "email": "",
  "mainLine": "mid",
  "subLine": "top",
  "tierTop": "gold",
  "tierJungle": "silver",
  "tierMid": "platinum",
  "tierAdc": "bronze",
  "tierSupport": "iron",
  "question": "pet",
  "answer": "멍멍이",
  "serviceTerms": true,
  "privacyTerms": true,
  "ageTerms": true,
  "marketingTerms": false,
  "eventTerms": false,
  "created_at": "2026-03-30T10:30:00Z"
}
```

### 프로필 조회 (GET /api/accounts/profile/)

**요청 헤더:**
```
Authorization: Bearer {access_token}
```

**응답 예시:**
```json
{
  "id": 1,
  "username": "hong123",
  "email": "",
  "mainLine": "mid",
  "subLine": "top",
  "tierTop": "gold",
  "tierJungle": "silver",
  "tierMid": "platinum",
  "tierAdc": "bronze",
  "tierSupport": "iron",
  "question": "pet",
  "answer": "멍멍이",
  "serviceTerms": true,
  "privacyTerms": true,
  "ageTerms": true,
  "marketingTerms": false,
  "eventTerms": false,
  "created_at": "2026-03-30T10:30:00Z"
}
```

**주의:** 비밀번호(`userPw`)는 보안을 위해 응답에 포함되지 않습니다.

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
