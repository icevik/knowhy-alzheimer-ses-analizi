from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_db
from app.models.participant import Participant, GroupType
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter()


class ParticipantCreate(BaseModel):
    name: str
    age: int
    gender: str
    group_type: GroupType
    mmse_score: int | None = None


class ParticipantResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    group_type: str
    mmse_score: int | None
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=ParticipantResponse)
async def create_participant(
    participant: ParticipantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_participant = Participant(
        user_id=current_user.id,
        **participant.dict()
    )
    db.add(db_participant)
    await db.commit()
    await db.refresh(db_participant)
    return db_participant


@router.get("/", response_model=List[ParticipantResponse])
async def get_participants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Participant).where(Participant.user_id == current_user.id)
    )
    participants = result.scalars().all()
    return participants


@router.get("/{participant_id}", response_model=ParticipantResponse)
async def get_participant(
    participant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Participant).where(
            Participant.id == participant_id,
            Participant.user_id == current_user.id
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Katılımcı bulunamadı")
    return participant
