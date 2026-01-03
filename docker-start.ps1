# TUBITAK Ses Analiz Platformu - Docker Başlatma Scripti (PowerShell)

Write-Host "KNOWHY Alzheimer Analiz Platformu - Docker Başlatılıyor..." -ForegroundColor Cyan

# .env dosyası kontrolü
if (-not (Test-Path .env)) {
    Write-Host "UYARI: .env dosyası bulunamadı!" -ForegroundColor Yellow
    Write-Host "Lütfen .env.example dosyasını kopyalayıp .env olarak oluşturun ve OPENAI_API_KEY değerini girin." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Komut: Copy-Item .env.example .env" -ForegroundColor Cyan
    exit 1
}

# Docker compose ile başlat
Write-Host "Docker container'ları başlatılıyor..." -ForegroundColor Green
docker-compose up -d

Write-Host ""
Write-Host "✅ Servisler başlatıldı!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Dokümantasyonu: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logları görmek için: docker-compose logs -f" -ForegroundColor Yellow
Write-Host "Durdurmak için: docker-compose down" -ForegroundColor Yellow

