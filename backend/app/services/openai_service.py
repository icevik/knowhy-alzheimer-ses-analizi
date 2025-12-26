import os
import asyncio
import json
from openai import OpenAI
from app.core.config import settings
from typing import Optional


class OpenAIService:
    def __init__(self):
        client_kwargs = {}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        self.client = OpenAI(
            api_key=settings.openai_api_key,
            **client_kwargs,
        )
    
    async def transcribe_audio(self, audio_path: str, language: str = "tr") -> str:
        """Whisper API ile ses dosyasını transkribe et"""
        def _transcribe():
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.openai_whisper_model,
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
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
        
        def _analyze():
            response = self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Sen bir nöroloji araştırmacısısın. Analiz sonuçlarını JSON formatında döndür.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                timeout=settings.openai_timeout_seconds,
            )
            result = json.loads(response.choices[0].message.content)
            return result
        
        return await asyncio.to_thread(_analyze)


openai_service = OpenAIService()

