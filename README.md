# Alzheimer Analizi Projesi (Powered by KNOWHY)

Alzheimer ve MCI (Hafif Bilişsel Bozukluk) tespiti için ses kayıtlarını analiz eden, **KNOWHY** tarafından desteklenen kapsamlı web platformu.

## Özellikler

### 🔐 Güvenlik ve Kimlik Doğrulama
- **Kullanıcı Kayıt ve Giriş**: Güvenli e-posta ve şifre ile giriş.
- **İki Aşamalı Doğrulama**: E-posta ile gönderilen kod ile hesap güvenliği.
- **Kullanıcı İzolasyonu**: Her kullanıcı sadece kendi katılımcılarını ve analizlerini görebilir.
- **Rate Limiting**: Giriş denemeleri ve e-posta gönderimleri için kötüye kullanım koruması.
- **Hesap Kilitleme**: Başarısız giriş denemeleri sonrası geçici hesap kilitleme.

### 🎙️ Analiz Yetenekleri
- **Ses Transkripsiyonu**: OpenAI Whisper API ile yüksek doğruluklu Türkçe metin dökümü.
- **Akustik Analiz**: `librosa` kütüphanesi ile detaylı ses öznitelikleri (pitch, enerji, jitter, shimmer vb.) çıkarma.
- **Yapay Zeka Raporlama**: GPT-4 ve Gemini modelleri ile transkript ve akustik verilerin derinlemesine klinik analizi.
- **Duygu ve İçerik Analizi**: Konuşma içeriğinin tutarlılığı ve duygusal durum analizi.

### 📋 Yönetim
- **Esnek Katılımcı Yönetimi**: Yaş sınırı olmaksızın katılımcı kaydı (Alzheimer, MCI, Kontrol grupları).
- **Detaylı Raporlama**: Her analiz için indirilebilir PDF raporlar ve grup bazlı istatistikler.

## Teknolojiler

### Backend
- **FastAPI**: Yüksek performanslı asenkron Python web framework'ü.
- **PostgreSQL**: Güvenilir ve ölçeklenebilir veritabanı.
- **SQLAlchemy (Async)**: Modern ORM yapısı.
- **JWT & Security**: `PyJWT`, `bcrypt` ve `passlib` ile güvenli kimlik doğrulama.
- **AI Entegrasyonu**: OpenAI ve OpenRouter API entegrasyonları.

### Frontend
- **React + TypeScript**: Güçlü tip desteği ile modern arayüz.
- **Vite**: Hızlı geliştirme ve build aracı.
- **Modern UI**: Koyu tema, glassmorphism efektleri ve responsive tasarım.

## Kurulum ve Çalıştırma (Docker)

### Gereksinimler
- Docker ve Docker Compose

### Adım Adım Kurulum

1. **Projeyi Klonlayın ve Dizine Girin**
   ```bash
   cd tubitak_voiceanalyzer
   ```

2. **Çevresel Değişkenleri Ayarlayın (.env)**
   Örnek dosyadan bir `.env` dosyası oluşturun:
   
   **Windows (PowerShell):**
   ```powershell
   Copy-Item .env.example .env
   ```
   **Linux/Mac:**
   ```bash
   cp .env.example .env
   ```

3. **.env Dosyasını Düzenleyin**
   Aşağıdaki değerleri kendi API anahtarlarınızla güncelleyin:
   ```env
   # OpenAI (Whisper ve GPT-4 için zorunlu)
   OPENAI_API_KEY=sk-...

   # OpenRouter (Klinik raporlar için - opsiyonel ama önerilir)
   OPENROUTER_API_KEY=sk-or-...
   OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

   # Güvenlik (JWT ve Webhook)
   JWT_SECRET_KEY=cok-guclu-ve-gizli-rastgele-bir-anahtar-olusturun
   EMAIL_WEBHOOK_URL=https://hook.eu2.make.com/... (E-posta gönderimi için webhook URL)
   ```

4. **Uygulamayı Başlatın**
   
   **Windows (PowerShell):**
   ```powershell
   docker-compose up -d --build
   ```

5. **Uygulamaya Erişin**
   - **Frontend (Arayüz):** [http://localhost:3000](http://localhost:3000)
   - **Backend API:** [http://localhost:8000](http://localhost:8000)
   - **Swagger Dokümantasyonu:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Kullanım Rehberi

1. **Kayıt Olun**: "Kayıt Ol" sayfasından e-posta ve şifrenizle hesap oluşturun. E-postanıza gelen kodu girerek hesabınızı doğrulayın.
2. **Giriş Yapın**: Bilgilerinizle giriş yapın (2. aşama doğrulamayı tamamlayın).
3. **Katılımcı Ekleyin**: Menüden "Yeni Katılımcı"ya tıklayın. İsim, yaş, cinsiyet ve grup tipi bilgilerini girin.
4. **Analiz Yapın**: "Ses Analizi" sayfasında kayıtlı bir katılımcı seçin ve ses dosyasını yükleyin. Analizi başlatın.
5. **Sonuçları İnceleyin**: Analiz tamamlandığında detaylı sonuç ekranına yönlendirilirsiniz. Buradan PDF raporunu indirebilirsiniz.

## Geliştirici Notları

- **Veritabanı Sıfırlama**: Şema değişikliklerinde veritabanını temizlemek için:
  ```bash
  docker-compose down -v
  docker-compose up -d --build
  ```
- **Logları İzleme**:
  ```bash
  docker-compose logs -f backend
  ```

---
*Bu proje KNOWHY tarafından desteklenmektedir.*
