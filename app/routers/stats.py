# app/routers/stats.py
from __future__ import annotations
import uuid
from typing import Dict
from sqlalchemy import select
from app.models.adventure import Adventure
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.stats import UserKCMastery, AdventureKCStat, AdventureSummary

from app.schemas.stats import (
    UserKCMasteryListOut, UserKCMasteryPatchIn, KCMastery,
    AdventureKCStatOut, AdventureKCStatPatchIn,
    AdventureSummaryOut, AdventureSummaryPatchIn,
    AdventureSummaryWithIdOut,        # ← add this
)

router = APIRouter()

# ---------- User KC Mastery ----------

@router.get("/mastery", response_model=UserKCMasteryListOut)
async def get_user_mastery(me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserKCMastery).where(UserKCMastery.user_id == me.id))
    rows = res.scalars().all()
    by_kc: Dict[int, UserKCMastery] = {r.kc_id: r for r in rows}

    out = []
    # Always return KC 1..20 with zeros when missing
    for kc in range(1, 21):
        r = by_kc.get(kc)
        out.append(KCMastery(
            kc_id=kc,
            p_know=(r.p_know if r else 0),
            correct=(r.correct if r else 0),
            incorrect=(r.incorrect if r else 0),
            best_sentence=(r.best_sentence if r else None),
            best_sentence_power=(r.best_sentence_power if r else None),
        ))
    return UserKCMasteryListOut(mastery=out)

@router.patch("/mastery", response_model=UserKCMasteryListOut)
async def upsert_user_mastery(payload: UserKCMasteryPatchIn, me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(UserKCMastery).where(UserKCMastery.user_id == me.id))
    existing = {r.kc_id: r for r in res.scalars().all()}

    for e in payload.mastery:
        row = existing.get(e.kc_id)
        if row is None:
            row = UserKCMastery(user_id=me.id, kc_id=e.kc_id)
            db.add(row)
        row.p_know = e.p_know
        row.correct = e.correct
        row.incorrect = e.incorrect
        row.best_sentence = e.best_sentence
        row.best_sentence_power = e.best_sentence_power

    await db.commit()
    return await get_user_mastery(me, db)

# ---------- Adventure KC Stats ----------

@router.get("/adventures/{adventure_id}/kc", response_model=list[AdventureKCStatOut])
async def get_adventure_kc_stats(adventure_id: str, me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        adv_id = uuid.UUID(adventure_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid adventure_id")
    res = await db.execute(select(AdventureKCStat).where(AdventureKCStat.adventure_id == adv_id))
    rows = res.scalars().all()
    return [
        AdventureKCStatOut(
            kc_id=r.kc_id, correct=r.correct, incorrect=r.incorrect,
            p_know=r.p_know, best_sentence=r.best_sentence, best_sentence_power=r.best_sentence_power
        )
        for r in rows
    ]

@router.patch("/adventures/{adventure_id}/kc", response_model=list[AdventureKCStatOut])
async def upsert_adventure_kc_stats(adventure_id: str, payload: AdventureKCStatPatchIn, me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        adv_id = uuid.UUID(adventure_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid adventure_id")
    res = await db.execute(select(AdventureKCStat).where(AdventureKCStat.adventure_id == adv_id))
    existing = {r.kc_id: r for r in res.scalars().all()}

    for e in payload.stats:
        row = existing.get(e.kc_id)
        if row is None:
            row = AdventureKCStat(adventure_id=adv_id, kc_id=e.kc_id)
            db.add(row)
        row.correct = e.correct
        row.incorrect = e.incorrect
        row.p_know = e.p_know
        row.best_sentence = e.best_sentence
        row.best_sentence_power = e.best_sentence_power

    await db.commit()
    return await get_adventure_kc_stats(adventure_id, me, db)

# ---------- Adventure Summary ----------

@router.get("/adventures/{adventure_id}/summary", response_model=AdventureSummaryOut)
async def get_adventure_summary(adventure_id: str, me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        adv_id = uuid.UUID(adventure_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid adventure_id")
    res = await db.execute(select(AdventureSummary).where(AdventureSummary.adventure_id == adv_id))
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")
    return AdventureSummaryOut(
        status=row.status,
        day_in_epoch_time=row.day_in_epoch_time,
        highest_floor_cleared=row.highest_floor_cleared,
        time_spent_seconds=row.time_spent_seconds,
        items_collected_json=row.items_collected_json,
        node_types_cleared_json=row.node_types_cleared_json,
        level=row.level,
        enemy_level=row.enemy_level,
        enemies_defeated=row.enemies_defeated,
        best_kc_id=row.best_kc_id,
        worst_kc_id=row.worst_kc_id,
        best_sentence=row.best_sentence,
    )

@router.patch("/adventures/{adventure_id}/summary", response_model=AdventureSummaryOut)
async def patch_adventure_summary(adventure_id: str, payload: AdventureSummaryPatchIn, me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        adv_id = uuid.UUID(adventure_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid adventure_id")
    res = await db.execute(select(AdventureSummary).where(AdventureSummary.adventure_id == adv_id))
    row = res.scalar_one_or_none()
    if not row:
        row = AdventureSummary(adventure_id=adv_id, status="Success", day_in_epoch_time=0,
                               highest_floor_cleared=0, time_spent_seconds=0,
                               level=1, enemy_level=1, enemies_defeated=0)
        db.add(row)

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)

    await db.commit()
    return await get_adventure_summary(adventure_id, me, db)

@router.get("/history", response_model=list[AdventureSummaryWithIdOut])
async def list_adventure_history(me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = (
        select(AdventureSummary)
        .join(AdventureSummary.adventure)              # FK → Adventure
        .where(Adventure.user_id == me.id)            # only my adventures
        .order_by(AdventureSummary.day_in_epoch_time.desc())
    )
    rows = (await db.execute(q)).scalars().all()

    return [
        AdventureSummaryWithIdOut(
            adventure_id=str(r.adventure_id),
            status=r.status,
            day_in_epoch_time=r.day_in_epoch_time,
            highest_floor_cleared=r.highest_floor_cleared,
            time_spent_seconds=r.time_spent_seconds,
            items_collected_json=r.items_collected_json,
            node_types_cleared_json=r.node_types_cleared_json,
            level=r.level,
            enemy_level=r.enemy_level,
            enemies_defeated=r.enemies_defeated,
            best_kc_id=r.best_kc_id,
            worst_kc_id=r.worst_kc_id,
            best_sentence=r.best_sentence,
        )
        for r in rows
    ]