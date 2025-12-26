# TUBITAK Ses Analiz Platformu

Alzheimer ve MCI (Hafif Bilişsel Bozukluk) tespiti için ses kayıtlarını analiz eden web tabanlı platform.

## Özellikler

- **Ses Transkripsiyonu**: OpenAI Whisper API ile Türkçe ses kayıtlarını metne dönüştürme
- **Akustik Analiz**: librosa kütüphanesi ile ses özelliklerini çıkarma (enerji, pitch, MFCC, vb.)
- **İçerik ve Duygu Analizi**: GPT-4 ile transkript ve akustik verilerin analizi
- **Katılımcı Yönetimi**: Alzheimer, MCI ve kontrol grupları için katılımcı kayıt sistemi
- **Raporlama**: Grup bazlı istatistikler ve analiz sonuçları

## Teknolojiler

### Backend
- FastAPI (Python)
- PostgreSQL (async)
- OpenAI API (Whisper + GPT-4)
- librosa (ses analizi)

### Frontend
- React + TypeScript
- Vite
- React Router

## Kurulum (Docker)

### Gereksinimler
- Docker ve Docker Compose
- OpenAI API anahtarı (Whisper ve GPT-4 için)
- OpenRouter API anahtarı (opsiyonel, klinik rapor için)

### Hızlı Başlangıç

1. **Proje dizinine gidin**
```bash
cd TUBITAK_voiceanalyzer
```

2. **.env dosyası oluşturun**
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

3. **.env dosyasını düzenleyin ve API anahtarlarınızı ekleyin**
```
# OpenAI API (Whisper transkripsiyon ve GPT-4 analiz için)
OPENAI_API_KEY=sk-your-api-key-here

# OpenRouter API (Klinik rapor oluşturma için - opsiyonel)
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
```

4. **Docker Compose ile başlatın**

**Windows PowerShell:**
```powershell
.\docker-start.ps1
```

**Linux/Mac:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

**Veya manuel olarak:**
```bash
docker-compose up -d
```

5. **Servislere erişim**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Dokümantasyonu: http://localhost:8000/docs

### Docker Komutları

```bash
# Servisleri başlat
docker-compose up -d

# Logları görüntüle
docker-compose logs -f

# Tüm servislerin logları
docker-compose logs -f backend frontend postgres

# Servisleri durdur
docker-compose down

# Servisleri durdur ve volume'leri sil (veritabanı verileri silinir)
docker-compose down -v

# Servisleri yeniden başlat
docker-compose restart

# Container durumunu kontrol et
docker-compose ps
```

## Kullanım

1. **Yeni Katılımcı Ekle**: Dashboard'dan "Yeni Katılımcı" sayfasına gidin ve katılımcı bilgilerini girin.

2. **Ses Analizi**: "Ses Analizi" sayfasından:
   - Bir katılımcı seçin
   - WAV, MP3, M4A veya WEBM formatında ses dosyası yükleyin
   - "Analiz Et" butonuna tıklayın

3. **Sonuçları Görüntüle**: Analiz tamamlandıktan sonra sonuçlar sayfasında:
   - Transkript metni
   - Duygu analizi (ton, yoğunluk, duygular)
   - İçerik analizi (kelime sayısı, akıcılık, tutarlılık)
   - Akustik özellikler (süre, enerji, pitch, tempo)

## API Endpoints

- `POST /api/participants/` - Yeni katılımcı oluştur
- `GET /api/participants/` - Tüm katılımcıları listele
- `GET /api/participants/{id}` - Katılımcı detayı
- `POST /api/analyze/` - Ses dosyası analiz et
- `GET /api/results/{id}` - Analiz sonucu getir
- `GET /api/reports/statistics` - İstatistikler

## Geliştirme

### Backend geliştirme
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend geliştirme
```bash
cd frontend
npm install
npm run dev
```

## Notlar

- Ses dosyaları maksimum 25MB olabilir
- OpenAI API kullanımı için ücretlendirme geçerlidir
- OpenRouter API anahtarı opsiyoneldir - yoksa temel analiz yapılır ancak klinik rapor oluşturulmaz
- Veritabanı verileri Docker volume'ünde saklanır

## OpenRouter Yapılandırması

Klinik rapor oluşturma için OpenRouter kullanılır. OpenRouter üzerinden çeşitli AI modellerine erişebilirsiniz:

1. [OpenRouter](https://openrouter.ai/) hesabı oluşturun
2. API anahtarı alın
3. İstediğiniz modeli seçin (örnek: `google/gemini-2.0-flash-exp:free`, `anthropic/claude-3-opus`, vb.)
4. `.env` dosyasına ekleyin:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
   ```

