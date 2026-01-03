#!/bin/bash

echo "KNOWHY Alzheimer Analiz Platformu - Docker Başlatılıyor..."

# .env dosyası kontrolü
if [ ! -f .env ]; then
    echo "UYARI: .env dosyası bulunamadı!"
    echo "Lütfen .env.example dosyasını kopyalayıp .env olarak oluşturun ve OPENAI_API_KEY değerini girin."
    echo ""
    echo "Komut: cp .env.example .env"
    exit 1
fi

# Docker compose ile başlat
echo "Docker container'ları başlatılıyor..."
docker-compose up -d

echo ""
echo "✅ Servisler başlatıldı!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Dokümantasyonu: http://localhost:8000/docs"
echo ""
echo "Logları görmek için: docker-compose logs -f"
echo "Durdurmak için: docker-compose down"

