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
