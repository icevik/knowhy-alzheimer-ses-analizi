import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.participant import Participant, GroupType
from app.models.analysis import Analysis
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Kullanıcının toplam katılımcı sayısı
    total_participants = await db.scalar(
        select(func.count(Participant.id)).where(Participant.user_id == current_user.id)
    )
    
    # Grup bazlı katılımcı sayıları
    group_counts = {}
    for group in GroupType:
        count = await db.scalar(
            select(func.count(Participant.id)).where(
                Participant.group_type == group,
                Participant.user_id == current_user.id
            )
        )
        group_counts[group.value] = count
    
    # Kullanıcının toplam analiz sayısı
    total_analyses = await db.scalar(
        select(func.count(Analysis.id)).where(Analysis.user_id == current_user.id)
    )
    
    # Ortalama MMSE skorları (grup bazlı)
    avg_mmse = {}
    for group in GroupType:
        result = await db.execute(
            select(func.avg(Participant.mmse_score)).where(
                Participant.group_type == group,
                Participant.user_id == current_user.id,
                Participant.mmse_score.isnot(None)
            )
        )
        avg = result.scalar()
        avg_mmse[group.value] = round(avg, 2) if avg else None
    
    return {
        "total_participants": total_participants,
        "group_counts": group_counts,
        "total_analyses": total_analyses,
        "average_mmse_scores": avg_mmse
    }


@router.get("/group/{group_type}")
async def get_group_reports(
    group_type: GroupType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Kullanıcının grup katılımcıları
    result = await db.execute(
        select(Participant).where(
            Participant.group_type == group_type,
            Participant.user_id == current_user.id
        )
    )
    participants = result.scalars().all()
    
    # Her katılımcının analizlerini getir
    reports = []
    for participant in participants:
        analyses_result = await db.execute(
            select(Analysis).where(
                Analysis.participant_id == participant.id,
                Analysis.user_id == current_user.id
            )
        )
        analyses = analyses_result.scalars().all()
        
        reports.append({
            "participant": {
                "id": participant.id,
                "name": participant.name,
                "age": participant.age,
                "gender": participant.gender,
                "mmse_score": participant.mmse_score
            },
            "analyses_count": len(analyses),
            "analyses": [
                {
                    "id": a.id,
                    "transcript": a.transcript,
                    "emotion_analysis": a.emotion_analysis,
                    "content_analysis": a.content_analysis,
                    "created_at": a.created_at.isoformat()
                }
                for a in analyses
            ]
        })
    
    return {
        "group_type": group_type.value,
        "participants": reports
    }


@router.get("/pdf/{analysis_id}")
async def download_report_pdf(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analiz raporunu PDF olarak indir"""
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı veya erişim izniniz yok")
    
    if not analysis.report_pdf_path or not os.path.exists(analysis.report_pdf_path):
        raise HTTPException(
            status_code=404, 
            detail="PDF raporu bulunamadı. Lütfen analizi tekrar çalıştırın."
        )
    
    return FileResponse(
        analysis.report_pdf_path,
        media_type="application/pdf",
        filename=f"rapor_{analysis_id}.pdf"
    )
