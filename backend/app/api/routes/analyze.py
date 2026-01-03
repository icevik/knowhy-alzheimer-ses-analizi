import os
import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.analysis import Analysis
from app.models.participant import Participant
from app.models.user import User
from app.services.openai_service import openai_service
from app.services.audio_service import audio_service
from app.services.advanced_audio_service import advanced_audio_service
from app.services.linguistic_service import linguistic_service
from app.services.openrouter_service import openrouter_service
from app.services.report_service import report_service
from app.services.progress_store import set_progress, get_progress, clear_progress, subscribe, unsubscribe
from app.api.dependencies import get_current_user

router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)


@router.get("/progress/{progress_id}/stream")
async def stream_progress(progress_id: str):
    """SSE endpoint for real-time progress updates"""
    async def event_generator():
        queue = subscribe(progress_id)
        try:
            # Send current progress immediately
            current = get_progress(progress_id)
            if current:
                yield f"data: {json.dumps(current)}\n\n"
            
            # Wait for updates
            while True:
                try:
                    # Wait for new progress update with timeout
                    progress = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(progress)}\n\n"
                    
                    # Check if analysis is complete
                    if progress.get("status") in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe(progress_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/progress/{progress_id}")
async def get_analysis_progress(progress_id: str):
    """Get current progress for an analysis"""
    progress = get_progress(progress_id)
    if not progress:
        return {"current_step": 0, "message": "Analiz bulunamadı veya tamamlandı", "status": "unknown"}
    return progress


@router.post("/")
async def analyze_audio(
    participant_id: int = Form(...),
    file: UploadFile = File(...),
    progress_id: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Dosya formatı kontrolü
    if not file.filename.endswith(('.wav', '.mp3', '.m4a', '.webm')):
        raise HTTPException(
            status_code=400, 
            detail="Desteklenmeyen dosya formatı. wav, mp3, m4a veya webm olmalı."
        )
    
    # Dosya boyutu kontrolü
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"Dosya boyutu {settings.max_file_size / 1024 / 1024}MB'dan büyük olamaz."
        )
    
    # Katılımcı kontrolü - sadece kullanıcının kendi katılımcıları
    result = await db.execute(
        select(Participant).where(
            Participant.id == participant_id,
            Participant.user_id == current_user.id
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Katılımcı bulunamadı veya erişim izniniz yok")
    
    # Progress ID - frontend'den gelen veya yeni oluştur
    if not progress_id:
        progress_id = str(uuid.uuid4())
    
    # Dosyayı kaydet
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, file_name)
    
    set_progress(progress_id, 1, "Dosya yükleniyor...")
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    try:
        import time
        start_time = time.time()
        
        # 1. Temel akustik özellikleri çıkar
        set_progress(progress_id, 2, "Temel akustik özellikler çıkarılıyor...")
        print(f"[Analiz] 1/9 Temel akustik ozellikler cikariliyor...", flush=True)
        acoustic_features = audio_service.extract_features(file_path)
        print(f"[Analiz] 1/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        
        # 2. Gelişmiş akustik özellikleri çıkar
        set_progress(progress_id, 3, "Gelişmiş akustik analiz yapılıyor...")
        print(f"[Analiz] 2/9 Gelismis akustik ozellikler cikariliyor...", flush=True)
        advanced_acoustic = advanced_audio_service.extract_advanced_features(file_path)
        print(f"[Analiz] 2/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        
        # 3. Transkripsiyon
        set_progress(progress_id, 4, "Konuşma metne dönüştürülüyor (Whisper)...")
        print(f"[Analiz] 3/9 Transkripsiyon yapiliyor (OpenAI Whisper)...", flush=True)
        transcript = await openai_service.transcribe_audio(file_path, language="tr")
        print(f"[Analiz] 3/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        
        # 4. Dilbilimsel analiz
        set_progress(progress_id, 5, "Dilbilimsel analiz yapılıyor...")
        print(f"[Analiz] 4/9 Dilbilimsel analiz yapiliyor...", flush=True)
        linguistic_analysis = linguistic_service.analyze_text(transcript)
        print(f"[Analiz] 4/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        
        # 5. GPT-4 ile duygu ve içerik analizi
        set_progress(progress_id, 6, "Duygu ve içerik analizi yapılıyor...")
        print(f"[Analiz] 5/9 Duygu ve icerik analizi yapiliyor...", flush=True)
        analysis_result = await openai_service.analyze_content_and_emotion(
            transcript, acoustic_features
        )
        print(f"[Analiz] 5/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        
        # 6. Katılımcı bilgilerini hazırla
        participant_info = {
            "name": participant.name,
            "age": participant.age,
            "gender": participant.gender,
            "group_type": participant.group_type.value,
            "mmse_score": participant.mmse_score
        }
        
        # 7. OpenRouter ile kapsamlı klinik rapor oluştur
        set_progress(progress_id, 7, "AI klinik raporu oluşturuluyor...")
        clinical_report = None
        try:
            print(f"[Analiz] 6/9 Klinik rapor olusturuluyor (OpenRouter)...", flush=True)
            clinical_report = await openrouter_service.generate_clinical_report(
                participant_info=participant_info,
                transcript=transcript,
                acoustic_features=acoustic_features,
                advanced_acoustic=advanced_acoustic,
                linguistic_analysis=linguistic_analysis,
                emotion_analysis=analysis_result.get("emotion_analysis", {}),
                content_analysis=analysis_result.get("content_analysis", {})
            )
            print(f"[Analiz] 6/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        except Exception as report_error:
            print(f"[Analiz] 6/9 Klinik rapor olusturulamadi: {report_error}", flush=True)
            clinical_report = None
        
        # 8. PDF rapor oluştur
        set_progress(progress_id, 8, "PDF raporu hazırlanıyor...")
        pdf_path = None
        try:
            print(f"[Analiz] 7/9 PDF rapor olusturuluyor...", flush=True)
            pdf_path = report_service.create_pdf_report(
                participant_info=participant_info,
                transcript=transcript,
                acoustic_features=acoustic_features,
                advanced_acoustic=advanced_acoustic,
                linguistic_analysis=linguistic_analysis,
                emotion_analysis=analysis_result.get("emotion_analysis", {}),
                content_analysis=analysis_result.get("content_analysis", {}),
                gemini_report=clinical_report
            )
            print(f"[Analiz] 7/9 Tamamlandi ({time.time() - start_time:.1f}s)", flush=True)
        except Exception as pdf_error:
            print(f"[Analiz] 7/9 PDF raporu olusturulamadi: {pdf_error}", flush=True)
            pdf_path = None
        
        # 9. Veritabanına kaydet
        set_progress(progress_id, 9, "Veritabanına kaydediliyor...")
        print(f"[Analiz] 8/9 Veritabanina kaydediliyor...", flush=True)
        db_analysis = Analysis(
            user_id=current_user.id,
            participant_id=participant_id,
            audio_path=file_path,
            transcript=transcript,
            acoustic_features=acoustic_features,
            emotion_analysis=analysis_result.get("emotion_analysis"),
            content_analysis=analysis_result.get("content_analysis"),
            advanced_acoustic=advanced_acoustic,
            linguistic_analysis=linguistic_analysis,
            gemini_report=clinical_report,
            report_pdf_path=pdf_path
        )
        db.add(db_analysis)
        await db.commit()
        await db.refresh(db_analysis)
        
        total_time = time.time() - start_time
        print(f"[Analiz] TAMAMLANDI! Toplam sure: {total_time:.1f}s", flush=True)
        
        # Progress tamamlandı
        set_progress(progress_id, 9, "Analiz tamamlandı!", status="completed")
        
        # Kısa gecikme ile progress'i temizle
        await asyncio.sleep(1)
        clear_progress(progress_id)
        
        return {
            "id": db_analysis.id,
            "participant_id": participant_id,
            "transcript": transcript,
            "acoustic_features": acoustic_features,
            "advanced_acoustic": advanced_acoustic,
            "linguistic_analysis": linguistic_analysis,
            "emotion_analysis": analysis_result.get("emotion_analysis"),
            "content_analysis": analysis_result.get("content_analysis"),
            "gemini_report": clinical_report,
            "report_pdf_path": pdf_path,
            "created_at": db_analysis.created_at.isoformat(),
            "progress_id": progress_id
        }
    
    except HTTPException:
        set_progress(progress_id, 0, "Hata oluştu", status="error")
        clear_progress(progress_id)
        raise
    except Exception as e:
        # Hata durumunda dosyayı sil
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        set_progress(progress_id, 0, f"Hata: {str(e)}", status="error")
        clear_progress(progress_id)
        
        import traceback
        error_trace = traceback.format_exc()
        print(f"Analiz hatası: {error_trace}")
        
        # Veritabanı hatası kontrolü
        error_msg = str(e)
        if "does not exist" in error_msg or "column" in error_msg.lower():
            raise HTTPException(
                status_code=500, 
                detail="Veritabani hatasi: Tablo veya kolon eksik. Lutfen backend'i yeniden baslatin."
            )
        
        raise HTTPException(status_code=500, detail=f"Analiz hatasi: {error_msg}")
