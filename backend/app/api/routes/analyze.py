import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.analysis import Analysis
from app.models.participant import Participant
from app.services.openai_service import openai_service
from app.services.audio_service import audio_service
from app.services.advanced_audio_service import advanced_audio_service
from app.services.linguistic_service import linguistic_service
from app.services.openrouter_service import openrouter_service
from app.services.report_service import report_service

router = APIRouter()

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.reports_dir, exist_ok=True)


@router.post("/")
async def analyze_audio(
    participant_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
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
    
    # Katılımcı kontrolü
    result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Dosyayı kaydet
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, file_name)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    try:
        # 1. Temel akustik özellikleri çıkar
        acoustic_features = audio_service.extract_features(file_path)
        
        # 2. Gelişmiş akustik özellikleri çıkar
        advanced_acoustic = advanced_audio_service.extract_advanced_features(file_path)
        
        # 3. Transkripsiyon
        transcript = await openai_service.transcribe_audio(file_path, language="tr")
        
        # 4. Dilbilimsel analiz
        linguistic_analysis = linguistic_service.analyze_text(transcript)
        
        # 5. GPT-4 ile duygu ve içerik analizi
        analysis_result = await openai_service.analyze_content_and_emotion(
            transcript, acoustic_features
        )
        
        # 6. Katılımcı bilgilerini hazırla
        participant_info = {
            "name": participant.name,
            "age": participant.age,
            "gender": participant.gender,
            "group_type": participant.group_type.value,
            "mmse_score": participant.mmse_score
        }
        
        # 7. OpenRouter ile kapsamlı klinik rapor oluştur (optional - hata durumunda devam et)
        clinical_report = None
        try:
            clinical_report = await openrouter_service.generate_clinical_report(
                participant_info=participant_info,
                transcript=transcript,
                acoustic_features=acoustic_features,
                advanced_acoustic=advanced_acoustic,
                linguistic_analysis=linguistic_analysis,
                emotion_analysis=analysis_result.get("emotion_analysis", {}),
                content_analysis=analysis_result.get("content_analysis", {})
            )
        except Exception as report_error:
            print(f"Klinik rapor olusturulamadi: {report_error}")
            clinical_report = None
        
        # 8. PDF rapor oluştur (Gemini raporu yoksa da oluştur)
        pdf_path = None
        try:
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
        except Exception as pdf_error:
            print(f"PDF raporu olusturulamadi: {pdf_error}")
            pdf_path = None
        
        # 9. Veritabanına kaydet
        db_analysis = Analysis(
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
            "created_at": db_analysis.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Hata durumunda dosyayı sil
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
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

