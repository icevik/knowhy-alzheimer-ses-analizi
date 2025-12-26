import os
import asyncio
import json
from openai import OpenAI
from app.core.config import settings
from typing import Optional
import httpx


class OpenAIService:
    def __init__(self):
        client_kwargs = {
            "timeout": httpx.Timeout(settings.openai_timeout_seconds * 5, connect=10.0)  # Whisper için daha uzun timeout
        }
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        self.client = OpenAI(
            api_key=settings.openai_api_key,
            **client_kwargs,
        )
    
    async def transcribe_audio(self, audio_path: str, language: str = "tr") -> str:
        """Whisper API ile ses dosyasını transkribe et"""
        def _transcribe():
            print(f"[Whisper] Dosya boyutu: {os.path.getsize(audio_path) / 1024:.1f} KB", flush=True)
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.openai_whisper_model,
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
            print(f"[Whisper] Transkripsiyon tamamlandi, uzunluk: {len(transcript)} karakter", flush=True)
            return transcript
        return await asyncio.to_thread(_transcribe)
    
    async def analyze_content_and_emotion(
        self, 
        transcript: str, 
        acoustic_features: dict
    ) -> dict:
        """GPT-4 ile içerik ve duygu analizi yap"""
        prompt = f"""Sen bir nöroloji araştırmacısısın. Aşağıdaki transkript metnini ve ses özelliklerini analiz et.

TRANSCRİPT:
{transcript}

SES ÖZELLİKLERİ:
{acoustic_features}

Lütfen şu analizleri yap:

1. Duygu Analizi:
   - Duygu tonu (pozitif/negatif/nötr)
   - Duygu yoğunluğu (1-10 arası)
   - Tespit edilen duygular (üzüntü, korku, mutluluk, öfke, vb.)

2. İçerik Analizi:
   - Metin uzunluğu ve kelime sayısı
   - Kelime çeşitliliği
   - Anlatım biçimi (akıcılık, tutarlılık)
   - İçerik kalitesi değerlendirmesi

3. Dilsel Göstergeler:
   - Cümle yapısı karmaşıklığı
   - Tekrar eden ifadeler
   - Eksik veya yarım kalan cümleler

Lütfen sonuçları JSON formatında döndür:
{{
    "emotion_analysis": {{
        "tone": "pozitif/negatif/nötr",
        "intensity": 5,
        "emotions": ["mutluluk", "kaygı"]
    }},
    "content_analysis": {{
        "word_count": 150,
        "unique_words": 80,
        "fluency_score": 7,
        "coherence_score": 6
    }},
    "linguistic_indicators": {{
        "sentence_complexity": "orta",
        "repetitions": 2,
        "incomplete_sentences": 1
    }}
}}"""
        
        def _normalize_content_analysis(ca: dict) -> dict:
            """GPT-4'ün döndürdüğü farklı formatları normalize et"""
            normalized = {
                "word_count": 0,
                "unique_words": 0,
                "fluency_score": 0,
                "coherence_score": 0
            }
            
            # Direkt alanları kontrol et
            if "word_count" in ca:
                normalized["word_count"] = ca["word_count"]
            elif "text_length" in ca and isinstance(ca["text_length"], dict):
                normalized["word_count"] = ca["text_length"].get("approx_word_count", 0)
            
            if "unique_words" in ca:
                normalized["unique_words"] = ca["unique_words"]
            elif "kelime_cesitliligi" in ca:
                # Yüzde olarak verilmişse kelime sayısından hesapla
                diversity = ca.get("kelime_cesitliligi", {})
                if isinstance(diversity, dict):
                    normalized["unique_words"] = int(normalized["word_count"] * diversity.get("tekrar_orani", 0.5))
            
            if "fluency_score" in ca:
                normalized["fluency_score"] = ca["fluency_score"]
            elif "anlatim_bicimi" in ca and isinstance(ca["anlatim_bicimi"], dict):
                # Akıcılık değerlendirmesinden skor çıkar
                akicilik = ca["anlatim_bicimi"].get("akicilik", "")
                if "yüksek" in str(akicilik).lower():
                    normalized["fluency_score"] = 8
                elif "orta" in str(akicilik).lower():
                    normalized["fluency_score"] = 6
                else:
                    normalized["fluency_score"] = 4
            
            if "coherence_score" in ca:
                normalized["coherence_score"] = ca["coherence_score"]
            elif "anlatim_bicimi" in ca and isinstance(ca["anlatim_bicimi"], dict):
                tutarlilik = ca["anlatim_bicimi"].get("tutarlilik", "")
                if "yüksek" in str(tutarlilik).lower():
                    normalized["coherence_score"] = 8
                elif "orta" in str(tutarlilik).lower() or "kismi" in str(tutarlilik).lower():
                    normalized["coherence_score"] = 5
                else:
                    normalized["coherence_score"] = 4
            
            return normalized
        
        def _analyze():
            try:
                response = self.client.chat.completions.create(
                    model=settings.openai_chat_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Sen bir nöroloji araştırmacısısın. Analiz sonuçlarını KESINLIKLE belirtilen JSON formatında döndür. Farklı alan isimleri kullanma.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    timeout=settings.openai_timeout_seconds,
                )
                result = json.loads(response.choices[0].message.content)
                print(f"[GPT-4] Analiz sonucu alindi: {list(result.keys())}", flush=True)
                
                # content_analysis'i normalize et
                if "content_analysis" in result:
                    original_ca = result["content_analysis"]
                    result["content_analysis"] = _normalize_content_analysis(original_ca)
                    ca = result["content_analysis"]
                    print(f"[GPT-4] content_analysis (normalized): word_count={ca.get('word_count')}, unique_words={ca.get('unique_words')}, fluency={ca.get('fluency_score')}, coherence={ca.get('coherence_score')}", flush=True)
                else:
                    print(f"[GPT-4] UYARI: content_analysis bulunamadi, varsayilan degerler kullaniliyor", flush=True)
                    result["content_analysis"] = {
                        "word_count": 0,
                        "unique_words": 0,
                        "fluency_score": 0,
                        "coherence_score": 0
                    }
                
                return result
            except Exception as e:
                print(f"[GPT-4] HATA: {e}", flush=True)
                # Varsayılan değerler döndür
                return {
                    "emotion_analysis": {
                        "tone": "nötr",
                        "intensity": 5,
                        "emotions": []
                    },
                    "content_analysis": {
                        "word_count": 0,
                        "unique_words": 0,
                        "fluency_score": 0,
                        "coherence_score": 0
                    },
                    "linguistic_indicators": {
                        "sentence_complexity": "bilinmiyor",
                        "repetitions": 0,
                        "incomplete_sentences": 0
                    }
                }
        
        return await asyncio.to_thread(_analyze)


openai_service = OpenAIService()

