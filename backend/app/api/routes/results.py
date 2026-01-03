import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete, func
from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def get_all_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """Kullanıcının tüm analizlerini listele"""
    # Toplam sayı
    total_result = await db.execute(
        select(func.count(Analysis.id)).where(Analysis.user_id == current_user.id)
    )
    total = total_result.scalar() or 0
    
    # Analizleri getir
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == current_user.id)
        .order_by(desc(Analysis.created_at))
        .limit(limit)
        .offset(offset)
    )
    analyses = result.scalars().all()
    
    return {
        "total": total,
        "items": [
            {
                "id": a.id,
                "participant_id": a.participant_id,
                "transcript": (a.transcript[:100] + "...") if a.transcript and len(a.transcript) > 100 else (a.transcript or ""),
                "emotion_analysis": a.emotion_analysis,
                "content_analysis": a.content_analysis,
                "has_gemini_report": bool(a.gemini_report),
                "has_pdf": bool(a.report_pdf_path),
                "created_at": a.created_at.isoformat()
            }
            for a in analyses
        ]
    }


@router.get("/{analysis_id}")
async def get_analysis_result(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == current_user.id
            )
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analiz bulunamadı veya erişim izniniz yok")
        
        return {
            "id": analysis.id,
            "participant_id": analysis.participant_id,
            "transcript": analysis.transcript or "",
            "acoustic_features": analysis.acoustic_features or {},
            "advanced_acoustic": analysis.advanced_acoustic or None,
            "linguistic_analysis": analysis.linguistic_analysis or None,
            "emotion_analysis": analysis.emotion_analysis or {},
            "content_analysis": analysis.content_analysis or {},
            "gemini_report": analysis.gemini_report or None,
            "report_pdf_path": analysis.report_pdf_path or None,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analiz alınırken hata: {str(e)}")


@router.get("/participant/{participant_id}")
async def get_participant_analyses(
    participant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.participant_id == participant_id,
            Analysis.user_id == current_user.id
        )
    )
    analyses = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "transcript": a.transcript,
            "acoustic_features": a.acoustic_features,
            "advanced_acoustic": a.advanced_acoustic,
            "linguistic_analysis": a.linguistic_analysis,
            "emotion_analysis": a.emotion_analysis,
            "content_analysis": a.content_analysis,
            "gemini_report": a.gemini_report,
            "report_pdf_path": a.report_pdf_path,
            "created_at": a.created_at.isoformat()
        }
        for a in analyses
    ]


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analizi sil"""
    try:
        # Analizi bul
        result = await db.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == current_user.id
            )
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analiz bulunamadı veya erişim izniniz yok")
        
        # İlgili dosyaları sil
        files_to_delete = []
        if analysis.audio_path and os.path.exists(analysis.audio_path):
            files_to_delete.append(analysis.audio_path)
        if analysis.report_pdf_path and os.path.exists(analysis.report_pdf_path):
            files_to_delete.append(analysis.report_pdf_path)
        
        # Veritabanından sil
        await db.execute(delete(Analysis).where(Analysis.id == analysis_id))
        await db.commit()
        
        # Dosyaları sil
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Dosya silinirken hata ({file_path}): {e}")
        
        return {"message": "Analiz başarıyla silindi", "id": analysis_id}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analiz silinirken hata: {str(e)}")
