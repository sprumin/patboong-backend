if (-Not (Test-Path .env)) {
    Write-Host ".env 파일이 없습니다. .env.example을 복사하여 .env를 생성하세요." -ForegroundColor Red
    Write-Host "cp .env.example .env" -ForegroundColor Yellow
    exit 1
}

Write-Host "Building Docker image..." -ForegroundColor Green
docker build -t drf-backend .

Write-Host "Starting containers..." -ForegroundColor Green
docker-compose up -d

Write-Host "Waiting for database..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Running migrations..." -ForegroundColor Green
docker-compose exec backend python manage.py migrate

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "배포 완료!" -ForegroundColor Green
Write-Host "Backend URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "슈퍼유저 생성:" -ForegroundColor Yellow
Write-Host "  docker-compose exec backend python manage.py createsuperuser" -ForegroundColor White
Write-Host ""
Write-Host "로그 확인:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f backend" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
