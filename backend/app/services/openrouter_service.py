import os
import asyncio
import json
import httpx
from typing import Dict, Optional
from app.core.config import settings


class OpenRouterService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
        self.timeout = settings.openrouter_timeout_seconds
    
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
        """OpenRouter ile kapsamlı klinik rapor oluştur"""
        
        if not self.api_key:
            print("OpenRouter API anahtari yapilandirilmamis.")
            return None
        
        # Kapsamlı prompt oluştur
        prompt = self._build_comprehensive_prompt(
            participant_info=participant_info,
            transcript=transcript,
            acoustic_features=acoustic_features,
            advanced_acoustic=advanced_acoustic,
            linguistic_analysis=linguistic_analysis,
            emotion_analysis=emotion_analysis,
            content_analysis=content_analysis
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/knowhy-alzheimer-analysis",
                        "X-Title": "KNOWHY Alzheimer Analysis"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Sen bir nöroloji ve konuşma patolojisi uzmanısın. Ses analizi verilerini inceleyip kapsamlı, bilimsel ve profesyonel klinik raporlar hazırlıyorsun. Raporlarını Türkçe, detaylı ve anlaşılır bir dille yazıyorsun."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "top_p": 0.95,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        print(f"OpenRouter yanit formati beklenmedik: {result}")
                        return None
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"OpenRouter API hatasi: {error_msg}")
                    if response.status_code == 429:
                        raise Exception("OpenRouter API kotasi asildi. Lutfen daha sonra tekrar deneyin.")
                    raise Exception(f"OpenRouter API hatasi: {error_msg}")
                    
        except httpx.TimeoutException:
            raise Exception("OpenRouter API yanit vermedi. Zaman asimi olustu.")
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception("OpenRouter API kotasi asildi. Lutfen daha sonra tekrar deneyin veya API planinizi kontrol edin.")
            raise Exception(f"OpenRouter raporu olusturulamadi: {error_msg}")
    
    def _build_comprehensive_prompt(
        self,
        participant_info: Dict,
        transcript: str,
        acoustic_features: Dict,
        advanced_acoustic: Dict,
        linguistic_analysis: Dict,
        emotion_analysis: Dict,
        content_analysis: Dict
    ) -> str:
        """Kapsamlı prompt oluştur"""
        
        return f"""Aşağıdaki ses analizi verilerini inceleyip kapsamlı bir klinik rapor hazırla.

═══════════════════════════════════════════════════════════════
KATILIMCI BİLGİLERİ
═══════════════════════════════════════════════════════════════
• İsim: {participant_info.get('name', 'N/A')}
• Yaş: {participant_info.get('age', 'N/A')}
• Cinsiyet: {participant_info.get('gender', 'N/A')}
• Grup Tipi: {participant_info.get('group_type', 'N/A').upper()}
• MMSE Skoru: {participant_info.get('mmse_score', 'N/A')}

═══════════════════════════════════════════════════════════════
TRANSCRİPT (Konuşmanın Metne Dönüştürülmüş Hali)
═══════════════════════════════════════════════════════════════
{transcript}

═══════════════════════════════════════════════════════════════
TEMEL AKUSTİK ÖZELLİKLER
═══════════════════════════════════════════════════════════════
{json.dumps(acoustic_features, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
GELİŞMİŞ AKUSTİK ÖZELLİKLER
═══════════════════════════════════════════════════════════════
{json.dumps(advanced_acoustic, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
DİLBİLİMSEL ANALİZ
═══════════════════════════════════════════════════════════════
{json.dumps(linguistic_analysis, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
DUYGU ANALİZİ
═══════════════════════════════════════════════════════════════
{json.dumps(emotion_analysis, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
İÇERİK ANALİZİ
═══════════════════════════════════════════════════════════════
{json.dumps(content_analysis, indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════════
RAPOR İÇERİĞİ TALİMATLARI
═══════════════════════════════════════════════════════════════

Lütfen aşağıdaki bölümleri içeren profesyonel, bilimsel ve detaylı bir klinik rapor hazırla. Raporu Türkçe yaz ve her metrik için klinik yorum yap.

1. ÖZET VE GENEL DEĞERLENDİRME
   - Analiz tarihi ve katılımcı bilgileri
   - Genel ses ve konuşma kalitesi değerlendirmesi
   - Öne çıkan bulguların kısa özeti
   - Klinik önemi olan gözlemler

2. AKUSTİK BULGULAR VE SES KALİTESİ ANALİZİ
   
   Temel Ses Özellikleri:
   - Pitch (perde) analizi: Ortalama ve standart sapma değerlerini yorumla
   - Enerji analizi: Ses şiddeti ve dinamikleri
   - Tempo ve ritim: Konuşma hızı değerlendirmesi
   - Spektral özellikler: Ses kalitesi göstergeleri
   
   Gelişmiş Ses Metrikleri:
   - Jitter (ses perdesi değişkenliği): Normal değerlerle karşılaştır, patolojik önemi
   - Shimmer (ses şiddeti değişkenliği): Ses kalitesi göstergesi olarak yorumla
   - HNR (Harmonic-to-Noise Ratio): Ses kalitesi değerlendirmesi
   - Formant analizi (F1, F2, F3, F4): Vokal özellikler ve konuşma kalitesi
   - Voice Onset Time (VOT): Ses başlangıcı analizi
   
   Konuşma Akışı Metrikleri:
   - Duraklama analizi: Duraklama sayısı, süresi ve yüzdesi
   - Konuşma hızı: Normal değerlerle karşılaştırma
   - Akıcılık değerlendirmesi: Kesintiler ve düzensizlikler

3. DİLBİLİMSEL VE DİLSEL BULGULAR
   
   Kelime ve Sözcük Analizi:
   - Kelime çeşitliliği (Type-Token Ratio): Kelime dağarcığı zenginliği
   - Benzersiz kelime sayısı: Sözcük dağarcığı değerlendirmesi
   - Kelime tekrarları: Patolojik tekrar paternleri
   
   Cümle Yapısı ve Karmaşıklığı:
   - Ortalama cümle uzunluğu: Dilbilgisel karmaşıklık göstergesi
   - Cümle sayısı ve yapısı: Sözdizimsel analiz
   - Sözdizimsel karmaşıklık seviyesi: Değerlendirme ve yorum
   
   Konuşma Bozuklukları:
   - Hesitation marker'lar: "eee", "şey", "hmm" gibi belirsizlik ifadeleri
   - Tekrar eden ifadeler: Kelime ve cümle tekrarları
   - Bağlaç kullanımı: Konuşma akışı ve bağlantı analizi

4. KONUŞMA AKIŞI VE AKICILIK ANALİZİ
   - Konuşma hızı değerlendirmesi (kelime/dakika)
   - Duraklama paternleri ve analizi
   - Akıcılık skoru yorumu
   - Kesinti ve düzensizlik değerlendirmesi
   - Normal konuşma akışı ile karşılaştırma

5. DUYGUSAL DURUM VE İÇERİK ANALİZİ
   
   Duygu Durumu:
   - Tespit edilen duygusal ton (pozitif/negatif/nötr)
   - Duygu yoğunluğu değerlendirmesi
   - Belirgin duygular ve ifade şekilleri
   
   İçerik Kalitesi:
   - Kelime sayısı ve çeşitliliği
   - Tutarlılık skoru: Konuşmanın mantıksal tutarlılığı
   - İçerik zenginliği ve derinliği
   - Konuşma kalitesi değerlendirmesi

6. GRUP BAZLI KARŞILAŞTIRMA VE RİSK DEĞERLENDİRMESİ
   
   Katılımcının grubuna göre değerlendirme:
   - {participant_info.get('group_type', 'N/A').upper()} grubu için normal değerlerle karşılaştırma
   - Alzheimer, MCI ve Kontrol grupları için tipik bulgular
   - Grup içi pozisyon analizi
   
   Risk Faktörleri:
   - Patolojik göstergeler ve anormallikler
   - Erken uyarı işaretleri
   - İlerleme riski değerlendirmesi
   - Klinik önemi olan bulgular

7. SONUÇ VE KLİNİK ÖNERİLER
   
   Özet Bulgular:
   - En önemli bulguların özeti
   - Ses ve konuşma kalitesi genel değerlendirmesi
   - Dilbilimsel ve akustik bulguların sentezi
   
   Klinik Önemi:
   - Bulguların klinik anlamı
   - Patolojik önemi olan metrikler
   - Normal varyasyon mu yoksa patolojik bulgu mu?
   
   Takip ve Öneriler:
   - Önerilen takip süresi ve sıklığı
   - İzlenmesi gereken metrikler
   - Müdahale önerileri (varsa)
   - Ek değerlendirme gereksinimleri

═══════════════════════════════════════════════════════════════
ÖNEMLİ NOTLAR
═══════════════════════════════════════════════════════════════
- Raporu Türkçe, bilimsel ve profesyonel bir dille yaz
- Her metrik için sayısal değerleri belirt ve yorumla
- Normal değerlerle karşılaştırma yap
- Klinik önemi olan bulguları vurgula
- Grup tipine (Alzheimer/MCI/Kontrol) özel değerlendirme yap
- Önerileri somut ve uygulanabilir şekilde sun
- Raporu net, anlaşılır ve yapılandırılmış bir formatta yaz
- Her bölümü detaylı ve kapsamlı şekilde ele al"""


openrouter_service = OpenRouterService()

