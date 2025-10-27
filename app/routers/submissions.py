# app/routers/submissions.py
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.db import get_db
from app.core.security import get_current_user
from app.schemas.submission import SubmissionIn, SubmissionOut
from app.crud import adventure as adv_crud
from app.models.stats import UserKCMastery, AdventureKCStat
from app.models.adventure import Adventure
from app.services.grammar_service import check_sentence
from app.utils.idempotency import ensure_idempotent
from app.services.mastery import apply_submission_side_effects

router = APIRouter()


@router.post("", response_model=SubmissionOut)
async def submit(
    payload: SubmissionIn,
    me=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    # ─────────────────────────────
    # 1. Validate adventure ownership
    # ─────────────────────────────
    try:
        adv_id = uuid.UUID(payload.adventure_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid adventure_id")

    adv = await adv_crud.get_by_id(db, adv_id)
    if not adv or adv.user_id != me.id:
        raise HTTPException(status_code=404, detail="Adventure not found")
    if adv.state != "in_progress":
        raise HTTPException(status_code=409, detail="Adventure not active")

    # ─────────────────────────────
    # 2. Idempotency protection
    # ─────────────────────────────
    if idempotency_key:
        key = f"submit:{adv.id}:{idempotency_key}"
        if not await ensure_idempotent(key):
            raise HTTPException(status_code=409, detail="Duplicate submission")

    # ─────────────────────────────
    # 3. Grammar evaluation
    # ─────────────────────────────
    # res = await check_sentence(payload.sentence, payload.kc_id, payload.tier_id)
    res = await check_sentence(payload.sentence, payload.kc_id)
    is_correct = bool(res.get("is_correct", False))
    feedback = list(res.get("feedback", []))
    error_indices = list(res.get("error_indices", []))
    from_cache = res.get("from_cache", False)

    # ─────────────────────────────
    # 4. Read existing priors
    # ─────────────────────────────
    adv_prior = 0.5
    user_prior = 0.5

    q1 = await db.execute(
        select(AdventureKCStat).where(
            AdventureKCStat.adventure_id == adv.id,
            AdventureKCStat.kc_id == payload.kc_id,
        )
    )
    adv_stat = q1.scalar_one_or_none()
    if adv_stat:
        adv_prior = adv_stat.p_know / 100.0

    q2 = await db.execute(
        select(UserKCMastery).where(
            UserKCMastery.user_id == me.id,
            UserKCMastery.kc_id == payload.kc_id,
        )
    )
    mastery = q2.scalar_one_or_none()
    if mastery:
        user_prior = mastery.p_know / 100.0

    # ─────────────────────────────
    # 5. Practice mode (no mutations)
    # ─────────────────────────────
    if adv.is_practice or payload.is_practice:
        return SubmissionOut(
            is_correct=is_correct,
            error_indices=error_indices,
            feedback=feedback,
            p_know_adventure=adv_prior,
            p_know_overall=user_prior,
            from_cache=from_cache,
        )

    # ─────────────────────────────
    # 6. Update mastery tables
    # ─────────────────────────────
    try:
        await apply_submission_side_effects(
            db=db,
            user_id=me.id,
            adventure_id=adv.id,
            kc_id=payload.kc_id,
            is_correct=is_correct,
            best_sentence=payload.sentence,
            best_power=None,
        )

        # ─────────────────────────────
        # 7. Also update Adventures.correct/incorrect_submissions
        # ─────────────────────────────
        if is_correct:
            await db.execute(
                update(Adventure)
                .where(Adventure.id == adv.id)
                .values(correct_submissions=Adventure.correct_submissions + 1)
            )
        else:
            await db.execute(
                update(Adventure)
                .where(Adventure.id == adv.id)
                .values(incorrect_submissions=Adventure.incorrect_submissions + 1)
            )

        await db.commit()
        await db.refresh(adv)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Mastery update failed: {ex}")

    # ─────────────────────────────
    # 8. Re-read latest mastery values
    # ─────────────────────────────
    q1b = await db.execute(
        select(AdventureKCStat).where(
            AdventureKCStat.adventure_id == adv.id,
            AdventureKCStat.kc_id == payload.kc_id,
        )
    )
    adv_stat = q1b.scalar_one_or_none()
    q2b = await db.execute(
        select(UserKCMastery).where(
            UserKCMastery.user_id == me.id,
            UserKCMastery.kc_id == payload.kc_id,
        )
    )
    mastery = q2b.scalar_one_or_none()

    p_adv = (adv_stat.p_know / 100.0) if adv_stat else adv_prior
    p_user = (mastery.p_know / 100.0) if mastery else user_prior

    # ─────────────────────────────
    # 9. Return submission result
    # ─────────────────────────────
    return SubmissionOut(
        is_correct=is_correct,
        error_indices=error_indices,
        feedback=feedback,
        p_know_adventure=p_adv,
        p_know_overall=p_user,
        from_cache=from_cache,
    )
