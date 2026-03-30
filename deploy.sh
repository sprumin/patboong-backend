#!/bin/bash

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
sleep 10

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
