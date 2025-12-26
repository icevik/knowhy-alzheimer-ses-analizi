import os
import asyncio
import json
from typing import Dict, Optional
import google.generativeai as genai
from app.core.config import settings


class GeminiService:
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
        else:
            self.model = None
    
    async def generate_clinical_report(
        self,
        participant_info: Dict,
        transcript: str,
        acoustic_features: Dict,
        advanced_acoustic: Dict,
        linguistic_analysis: Dict,
        emotion_analysis: Dict,
        content_analysis: Dict
    ) -> Optional[str]:
        """Gemini ile kapsamlı klinik rapor oluştur"""
        
        if not self.model:
            return None
        
        # Rapor için prompt oluştur
        prompt = f"""Sen bir nöroloji ve konuşma patolojisi uzmanısın. Aşağıdaki ses analizi verilerini inceleyip kapsamlı bir klinik rapor hazırla.

KATILIMCI BİLGİLERİ:
- İsim: {participant_info.get('name', 'N/A')}
- Yaş: {participant_info.get('age', 'N/A')}
- Cinsiyet: {participant_info.get('gender', 'N/A')}
- Grup: {participant_info.get('group_type', 'N/A')}
- MMSE Skoru: {participant_info.get('mmse_score', 'N/A')}

TRANSCRİPT:
{transcript}

TEMEL AKUSTİK ÖZELLİKLER:
{json.dumps(acoustic_features, indent=2, ensure_ascii=False)}

GELİŞMİŞ AKUSTİK ÖZELLİKLER:
{json.dumps(advanced_acoustic, indent=2, ensure_ascii=False)}

DİLBİLİMSEL ANALİZ:
{json.dumps(linguistic_analysis, indent=2, ensure_ascii=False)}

DUYGU ANALİZİ:
{json.dumps(emotion_analysis, indent=2, ensure_ascii=False)}

İÇERİK ANALİZİ:
{json.dumps(content_analysis, indent=2, ensure_ascii=False)}

Lütfen aşağıdaki bölümleri içeren profesyonel bir klinik rapor hazırla:

1. ÖZET
   - Analiz tarihi ve katılımcı bilgileri
   - Genel değerlendirme

2. AKUSTİK BULGULAR
   - Temel ses özellikleri (pitch, energy, tempo)
   - Gelişmiş metrikler (jitter, shimmer, HNR)
   - Formant analizi
   - Ses kalitesi değerlendirmesi
   - Klinik yorum

3. DİLBİLİMSEL BULGULAR
   - Kelime çeşitliliği ve zenginliği
   - Cümle yapısı ve karmaşıklığı
   - Hesitation marker'lar ve duraklamalar
   - Tekrar eden ifadeler
   - Klinik yorum

4. KONUŞMA AKIŞI ANALİZİ
   - Konuşma hızı ve ritmi
   - Duraklama analizi
   - Akıcılık değerlendirmesi

5. DUYGUSAL VE İÇERİK ANALİZİ
   - Duygu durumu
   - İçerik kalitesi
   - Tutarlılık değerlendirmesi

6. GRUP KARŞILAŞTIRMASI
   - Katılımcının grubuna (Alzheimer/MCI/Kontrol) göre bulguların değerlendirilmesi
   - Normal değerlerle karşılaştırma
   - Risk faktörleri

7. SONUÇ VE ÖNERİLER
   - Özet bulgular
   - Klinik önemi
   - Takip önerileri
   - Önerilen müdahaleler

Raporu Türkçe, bilimsel ve profesyonel bir dille yaz. Metrikleri yorumla ve klinik önemlerini açıkla."""

        def _generate():
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 4096,
                    }
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                # Quota hatası kontrolü
                if "quota" in error_msg.lower() or "429" in error_msg:
                    raise Exception("Gemini API kotasi asildi. Lutfen daha sonra tekrar deneyin veya API planinizi kontrol edin.")
                # Diğer hatalar
                raise Exception(f"Gemini raporu olusturulamadi: {error_msg}")
        
        try:
            return await asyncio.to_thread(_generate)
        except Exception as e:
            # Hata durumunda None döndür, analiz devam etsin
            print(f"Gemini servisi hatasi: {e}")
            return None


gemini_service = GeminiService()

