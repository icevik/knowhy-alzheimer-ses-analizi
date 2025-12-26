"""In-memory progress store for analysis tracking"""
from typing import Dict, Optional
import asyncio

# Global progress store
_progress_store: Dict[str, Dict] = {}
_subscribers: Dict[str, list] = {}

ANALYSIS_STEPS = [
    {"step": 1, "title": "Dosya Yükleme", "description": "Ses dosyası yükleniyor..."},
    {"step": 2, "title": "Akustik Analiz", "description": "Temel akustik özellikler çıkarılıyor..."},
    {"step": 3, "title": "Gelişmiş Akustik", "description": "Jitter, shimmer, formant analizi..."},
    {"step": 4, "title": "Transkripsiyon", "description": "Konuşma metne dönüştürülüyor (Whisper)..."},
    {"step": 5, "title": "Dilbilimsel Analiz", "description": "Metin analizi yapılıyor..."},
    {"step": 6, "title": "Duygu Analizi", "description": "Duygu ve içerik analizi (GPT-4)..."},
    {"step": 7, "title": "Klinik Rapor", "description": "AI klinik raporu oluşturuluyor..."},
    {"step": 8, "title": "PDF Oluşturma", "description": "PDF rapor hazırlanıyor..."},
    {"step": 9, "title": "Kayıt", "description": "Veritabanına kaydediliyor..."},
]


def set_progress(progress_id: str, step: int, message: str = "", status: str = "running"):
    """Update progress for an analysis"""
    progress_data = {
        "current_step": step,
        "total_steps": len(ANALYSIS_STEPS),
        "message": message,
        "status": status,  # running, completed, error
        "steps": ANALYSIS_STEPS
    }
    _progress_store[progress_id] = progress_data
    print(f"[Progress] ID={progress_id[:8]}... Step={step} Message={message}", flush=True)
    
    # Notify subscribers
    if progress_id in _subscribers:
        for queue in _subscribers[progress_id]:
            try:
                queue.put_nowait(progress_data.copy())
            except:
                pass


def get_progress(progress_id: str) -> Optional[Dict]:
    """Get current progress for an analysis"""
    return _progress_store.get(progress_id)


def clear_progress(progress_id: str):
    """Clear progress after analysis is complete"""
    if progress_id in _progress_store:
        del _progress_store[progress_id]
    if progress_id in _subscribers:
        del _subscribers[progress_id]


def subscribe(progress_id: str) -> asyncio.Queue:
    """Subscribe to progress updates"""
    if progress_id not in _subscribers:
        _subscribers[progress_id] = []
    queue = asyncio.Queue()
    _subscribers[progress_id].append(queue)
    return queue


def unsubscribe(progress_id: str, queue: asyncio.Queue):
    """Unsubscribe from progress updates"""
    if progress_id in _subscribers and queue in _subscribers[progress_id]:
        _subscribers[progress_id].remove(queue)

