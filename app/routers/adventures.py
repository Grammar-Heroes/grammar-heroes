from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core.db import get_db
from app.schemas.adventure import AdventureOut, AdventureStartIn, AdventureProgressIn, AdventureFinishIn
from app.crud import adventure as adv_crud
from app.models.enums import AdventureState
from app.models.stats import AdventureSummary, AdventureKCStat
from app.utils.idempotency import ensure_idempotent

router = APIRouter()

# ──────────────────────────────────────────────
# START
# ──────────────────────────────────────────────
@router.post("/start", response_model=AdventureOut)
async def start(
    payload: AdventureStartIn,
    me = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    force_new: bool = Query(True),
):
    existing = await adv_crud.get_active_for_user(db, me.id)

    if existing and force_new:
        await adv_crud.abandon_active_for_user(db, me.id)
        existing = None

    adv = existing or await adv_crud.create(db, me.id, payload.is_practice, seed=payload.seed)

    return AdventureOut(
        id=str(adv.id),
        user_id=str(adv.user_id),
        state=adv.state,
        current_node_id=adv.current_node_id,
        current_node_kc=adv.current_node_kc,
        cleared_nodes=list(adv.cleared_nodes or []),
        items_collected=list(adv.items_collected or []),
        node_name=adv.node_name,
        current_floor=adv.current_floor,
        level=adv.level,
        add_writing_level=adv.add_writing_level,
        add_defense_level=adv.add_defense_level,
        enemy_level=adv.enemy_level,
        add_enemy_writing_level=adv.add_enemy_writing_level,
        add_enemy_defense_level=adv.add_enemy_defense_level,
        is_practice=adv.is_practice,
        seed=adv.seed,
        enemies_defeated=adv.enemies_defeated,
        reward_hero_pass_exp=adv.reward_hero_pass_exp,
        reward_notes=adv.reward_notes,
        node_types_cleared=list(adv.node_types_cleared or []),
        correct_submissions=adv.correct_submissions,
        incorrect_submissions=adv.incorrect_submissions,
        total_damage_dealt=adv.total_damage_dealt,
        total_damage_received=adv.total_damage_received,
        
        # ─── NEW FIELDS ───
        best_sentence=adv.best_sentence,
        best_sentence_power=adv.best_sentence_power,
        best_kc_id=adv.best_kc_id,
    )


# ──────────────────────────────────────────────
# PROGRESS
# ──────────────────────────────────────────────
@router.patch("/progress", response_model=AdventureOut)
async def progress(
    payload: AdventureProgressIn,
    me = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    adv = await adv_crud.get_active_for_user(db, me.id)
    if not adv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active adventure")

    data = {k: v for k, v in payload.model_dump().items() if v is not None and k != "seed"}
    adv = await adv_crud.update_partial(db, adv, data)

    return AdventureOut(
        id=str(adv.id),
        user_id=str(adv.user_id),
        state=adv.state,
        current_node_id=adv.current_node_id,
        current_node_kc=adv.current_node_kc,
        cleared_nodes=list(adv.cleared_nodes or []),
        items_collected=list(adv.items_collected or []),
        node_name=adv.node_name,
        current_floor=adv.current_floor,
        level=adv.level,
        add_writing_level=adv.add_writing_level,
        add_defense_level=adv.add_defense_level,
        enemy_level=adv.enemy_level,
        add_enemy_writing_level=adv.add_enemy_writing_level,
        add_enemy_defense_level=adv.add_enemy_defense_level,
        is_practice=adv.is_practice,
        seed=adv.seed,
        enemies_defeated=adv.enemies_defeated,
        reward_hero_pass_exp=adv.reward_hero_pass_exp,
        reward_notes=adv.reward_notes,
        node_types_cleared=list(adv.node_types_cleared or []),
        correct_submissions=adv.correct_submissions,
        incorrect_submissions=adv.incorrect_submissions,
        total_damage_dealt=adv.total_damage_dealt,
        total_damage_received=adv.total_damage_received,

        # ─── NEW FIELDS ───
        best_sentence=adv.best_sentence,
        best_sentence_power=adv.best_sentence_power,
        best_kc_id=adv.best_kc_id,
    )


# ──────────────────────────────────────────────
# FINISH
# ──────────────────────────────────────────────
@router.post("/finish")
async def finish(
    payload: AdventureFinishIn,
    me = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    adv = await adv_crud.get_active_for_user(db, me.id)
    if not adv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active adventure")

    if idempotency_key and not await ensure_idempotent(f"finish:{adv.id}:{idempotency_key}"):
        return {"message": "duplicate"}

    adv = await adv_crud.finish(db, adv, payload.status)

    adv.total_damage_dealt = payload.total_damage_dealt
    adv.total_damage_received = payload.total_damage_received
    adv.best_sentence = payload.best_sentence
    adv.best_sentence_power = payload.best_sentence_power

    res = await db.execute(select(AdventureKCStat).where(AdventureKCStat.adventure_id == adv.id))
    rows = res.scalars().all()

    best_kc, worst_kc = None, None
    best_val, worst_val = -1, 1e9
    for r in rows:
        val = r.correct - r.incorrect
        if val > best_val:
            best_val, best_kc = val, r.kc_id
        if val < worst_val:
            worst_val, worst_kc = val, r.kc_id

    adv.best_kc_id = best_kc

    summary = AdventureSummary(
        adventure_id=adv.id,
        status=payload.status,
        day_in_epoch_time=payload.day_in_epoch_time,
        highest_floor_cleared=payload.highest_floor_cleared,
        time_spent_seconds=payload.time_spent_seconds,
        items_collected_json=",".join(payload.items_collected or []),
        node_types_cleared_json=",".join(map(str, payload.node_types_cleared or [])),
        level=payload.level,
        enemy_level=payload.enemy_level,
        enemies_defeated=payload.enemies_defeated,
        best_kc_id=best_kc,
        worst_kc_id=worst_kc,
        best_sentence=payload.best_sentence,
        total_damage_dealt=payload.total_damage_dealt,
        total_damage_received=payload.total_damage_received,
    )

    from app.crud.adventure_stats import create_summary
    await create_summary(db, summary)

    if payload.status.lower() == "success":
        me.total_adventures_cleared += 1

    await db.commit()
    return {"ok": True}