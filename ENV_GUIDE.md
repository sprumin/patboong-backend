# Django DRF Backend - 환경변수 설정 가이드

## 필수 환경변수

### Django 설정
```
SECRET_KEY=your-very-secret-key-change-this-in-production-min-50-chars
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1,backend
```

**SECRET_KEY 생성 방법:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 데이터베이스 설정 (MySQL)
```
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=drf_backend
DATABASE_USER=drf_user
DATABASE_PASSWORD=your-strong-password
DATABASE_HOST=db
DATABASE_PORT=3306
```

**DATABASE_HOST 값:**
- Docker Compose 사용 시: `db` (서비스명)
- 외부 MySQL 사용 시: `mysql.example.com` 또는 IP 주소

### CORS 설정
```
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 배포 환경별 설정

### 로컬 개발
```bash
SECRET_KEY=dev-secret-key
DEBUG=True
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:3000
DATABASE_HOST=localhost
```

### Docker Compose
```bash
SECRET_KEY=production-secret-key-change-this
DEBUG=False
ALLOWED_HOSTS=localhost,backend
CORS_ALLOWED_ORIGINS=http://localhost:3000
DATABASE_HOST=db
```

### 프로덕션 (외부 MySQL)
```bash
SECRET_KEY=production-secret-key-50-chars-minimum-change-this-value
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DATABASE_HOST=mysql-prod.example.com
DATABASE_PORT=3306
```

## 보안 체크리스트

- [ ] SECRET_KEY를 50자 이상의 랜덤 문자열로 변경
- [ ] DEBUG=False로 설정 (프로덕션)
- [ ] ALLOWED_HOSTS에 실제 도메인만 포함
- [ ] 강력한 DB 비밀번호 사용
- [ ] .env 파일을 .gitignore에 추가
- [ ] CORS_ALLOWED_ORIGINS에 신뢰할 수 있는 도메인만 추가
