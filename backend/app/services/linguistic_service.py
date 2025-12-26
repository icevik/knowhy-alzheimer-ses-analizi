import re
import numpy as np
from typing import Dict, List
from collections import Counter


class LinguisticService:
    @staticmethod
    def analyze_text(transcript: str) -> Dict:
        """Dilbilimsel analiz: TTR, MLU, hesitation markers, tekrar analizi"""
        
        if not transcript or len(transcript.strip()) == 0:
            return {
                "type_token_ratio": 0.0,
                "mean_length_utterance": 0.0,
                "sentence_count": 0,
                "hesitation_markers": [],
                "hesitation_count": 0,
                "repetitions": [],
                "repetition_count": 0,
                "syntactic_complexity": "dusuk"
            }
        
        # Temizleme
        text = transcript.strip()
        
        # Cümle ayırma (basit - nokta, soru işareti, ünlem)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Kelime ayırma
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = len(words)
        
        # Benzersiz kelimeler
        unique_words = set(words)
        unique_word_count = len(unique_words)
        
        # Type-Token Ratio (TTR)
        ttr = unique_word_count / word_count if word_count > 0 else 0.0
        
        # Mean Length of Utterance (MLU) - Ortalama cümle uzunluğu
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        mlu = np.mean(sentence_lengths) if sentence_lengths else 0.0
        
        # Hesitation markers (Türkçe)
        hesitation_patterns = [
            r'\b(ııı|iii|eee|ehh|hmm|şey|yani|hani|işte)\b',
            r'\b(um|uh|er|ah)\b',
            r'\b(ıı|ee|aa)\b'
        ]
        
        hesitation_markers = []
        hesitation_count = 0
        
        for pattern in hesitation_patterns:
            matches = re.findall(pattern, text.lower())
            hesitation_markers.extend(matches)
            hesitation_count += len(matches)
        
        # Tekrar analizi - ardışık tekrar eden kelimeler
        repetitions = []
        repetition_count = 0
        
        if len(words) > 1:
            i = 0
            while i < len(words) - 1:
                if words[i] == words[i+1]:
                    # Tekrar serisini bul
                    repeat_word = words[i]
                    repeat_count = 2
                    j = i + 2
                    while j < len(words) and words[j] == repeat_word:
                        repeat_count += 1
                        j += 1
                    
                    if repeat_count >= 2:
                        repetitions.append({
                            "word": repeat_word,
                            "count": repeat_count,
                            "position": i
                        })
                        repetition_count += 1
                        i = j
                    else:
                        i += 1
                else:
                    i += 1
        
        # Sozdizimsel karmaşıklık (basit metrik)
        # Uzun cümleler ve bağlaç kullanımı
        avg_sentence_length = mlu
        conjunction_words = ['ve', 'ile', 'ama', 'fakat', 'ancak', 'çünkü', 'ki', 'daha', 'en']
        conjunction_count = sum(1 for w in words if w in conjunction_words)
        conjunction_ratio = conjunction_count / word_count if word_count > 0 else 0.0
        
        if avg_sentence_length > 15 and conjunction_ratio > 0.1:
            syntactic_complexity = "yuksek"
        elif avg_sentence_length > 10 and conjunction_ratio > 0.05:
            syntactic_complexity = "orta"
        else:
            syntactic_complexity = "dusuk"
        
        # Kelime çeşitliliği skoru
        diversity_score = ttr * 100  # 0-100 arası
        
        return {
            "word_count": word_count,
            "unique_word_count": unique_word_count,
            "type_token_ratio": float(ttr),
            "diversity_score": float(diversity_score),
            "mean_length_utterance": float(mlu),
            "sentence_count": len(sentences),
            "avg_sentence_length": float(avg_sentence_length),
            "hesitation_markers": list(set(hesitation_markers)),  # Benzersiz
            "hesitation_count": hesitation_count,
            "hesitation_ratio": float(hesitation_count / word_count) if word_count > 0 else 0.0,
            "repetitions": repetitions[:10],  # İlk 10 tekrar
            "repetition_count": repetition_count,
            "repetition_ratio": float(repetition_count / word_count) if word_count > 0 else 0.0,
            "conjunction_count": conjunction_count,
            "conjunction_ratio": float(conjunction_ratio),
            "syntactic_complexity": syntactic_complexity
        }


linguistic_service = LinguisticService()

