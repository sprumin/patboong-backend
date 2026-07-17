#!/bin/bash

set -euo pipefail

if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. .env.example을 복사하여 .env를 생성하세요."
    echo "   cp .env.example .env"
    exit 1
fi

echo "🔨 Building Docker image..."
docker-compose build --no-cache

echo "🚀 Starting containers..."
docker-compose up -d

echo "⏳ Waiting for database..."
db_attempt=1
db_max_attempts=30
until docker-compose exec -T backend python manage.py shell -c \
    "from django.db import connection; connection.ensure_connection()"; do
    if [ "$db_attempt" -ge "$db_max_attempts" ]; then
        echo "Database connection failed after $db_max_attempts attempts."
        docker-compose logs --tail=100 db
        exit 1
    fi

    echo "  database is not reachable from backend yet ($db_attempt/$db_max_attempts); retrying in 2s..."
    db_attempt=$((db_attempt + 1))
    sleep 2
done
echo "✅ Database is ready!"

echo "📦 Collecting static files..."
docker-compose exec backend python manage.py collectstatic --noinput

echo "📦 Running migrations..."
docker-compose exec backend python manage.py migrate

echo ""
echo "=================================================="
echo "✅ 배포 완료!"
echo "🌐 Backend URL: http://localhost:8000"
echo "🌐 API 문서 (Swagger): http://localhost:8000/api/docs/"
echo "🌐 API 문서 (ReDoc): http://localhost:8000/api/redoc/"
echo ""
echo "🔑 슈퍼유저 생성:"
echo "   docker-compose exec backend python manage.py createsuperuser"
echo ""
echo "📋 로그 확인:"
echo "   docker-compose logs -f backend"
echo "=================================================="
