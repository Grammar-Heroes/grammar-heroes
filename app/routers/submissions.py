from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert

from app.models.user import User
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

# BKT parameters
BKT_GUESS = 0.20
BKT_SLIP = 0.10
BKT_LEARN = 0.15


def _bkt_update(prior: float, is_correct: bool) -> float:
    """Return posterior probability using standard BKT."""
    p = prior
    if is_correct:
        numer = p * (1 - BKT_SLIP)
        denom = numer + (1 - p) * BKT_GUESS
    else:
        numer = p * BKT_SLIP
        denom = numer + (1 - p) * (1 - BKT_GUESS)
    p_evidence = 0.0 if denom == 0 else numer / denom
    return min(1.0, max(0.0, p_evidence + (1 - p_evidence) * BKT_LEARN))



@router.post("", response_model=SubmissionOut)
async def submit(
    payload: SubmissionIn,
    me: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """
    /submissions endpoint:
    - PRACTICE mode → ONLY updates UserKCMastery (no adventure validation, no UUID)
    - ADVENTURE mode → full validation + adventure-level updates
    """

    # ─────────────────────────────────────────────
    # PRACTICE MODE  ✅ no UUID, no Adventure lookup
    # (This section is unchanged)
    # ─────────────────────────────────────────────
    if payload.is_practice:
        # Grammar scoring
        res = await check_sentence(payload.sentence, payload.kc_id)
        is_correct = bool(res.get("is_correct", False))
        feedback = list(res.get("feedback", []))
        error_indices = list(res.get("error_indices", []))
        from_cache = res.get("from_cache", False)
        # Note: sentence_power from res is ignored here, as practice mode
        # doesn't update adventure-level stats.

        # Read existing user-level mastery
        user_prior = 0.5
        q = await db.execute(
            select(UserKCMastery).where(
                UserKCMastery.user_id == me.id,
                UserKCMastery.kc_id == payload.kc_id,
            )
        )
        mastery = q.scalar_one_or_none()
        if mastery:
            user_prior = mastery.p_know / 100.0

        # Compute updated p_know
        next_p = _bkt_update(user_prior, is_correct)

        try:
            if mastery is None:
                await db.execute(
                    insert(UserKCMastery).values(
                        user_id=me.id,
                        kc_id=payload.kc_id,
                        p_know=int(round(next_p * 100)),
                        correct=1 if is_correct else 0,
                        incorrect=0 if is_correct else 1,
                        best_sentence=payload.sentence if is_correct else None,
                        best_sentence_power=None, # UserKCMastery might not track power, or could use res.get("sentence_power")
                    )
                )
            else:
                await db.execute(
                    update(UserKCMastery)
                    .where(
                        UserKCMastery.user_id == me.id,
                        UserKCMastery.kc_id == payload.kc_id,
                    )
                    .values(
                        p_know=int(round(next_p * 100)),
                        correct=UserKCMastery.correct + (1 if is_correct else 0),
                        incorrect=UserKCMastery.incorrect + (0 if is_correct else 1),
                        best_sentence=(
                            payload.sentence
                            if is_correct
                            else UserKCMastery.best_sentence
                        ),
                        # best_sentence_power could also be updated here if needed
                    )
                )
            await db.commit()
        except Exception as ex:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Practice update failed: {ex}")

        # Adventure p_know stays unused in practice
        return SubmissionOut(
            is_correct=is_correct,
            error_indices=error_indices,
            feedback=feedback,
            p_know_adventure=0.5,  # irrelevant in practice mode
            p_know_overall=next_p,
            from_cache=from_cache,
        )

    # ─────────────────────────────────────────────
    # ADVENTURE MODE (normal behavior)
    # (This section is MODIFIED)
    # ─────────────────────────────────────────────
    try:
        adv_id = uuid.UUID(payload.adventure_id)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid adventure_id")

    adv = await adv_crud.get_by_id(db, adv_id)
    if not adv or adv.user_id != me.id:
        raise HTTPException(status_code=404, detail="Adventure not found")
    if adv.state != "in_progress":
        raise HTTPException(status_code=409, detail="Adventure not active")

    if idempotency_key:
        key = f"submit:{adv.id}:{idempotency_key}"
        if not await ensure_idempotent(key):
            raise HTTPException(status_code=409, detail="Duplicate submission")

    # Grammar check
    res = await check_sentence(payload.sentence, payload.kc_id)
    is_correct = bool(res.get("is_correct", False))
    feedback = list(res.get("feedback", []))
    error_indices = list(res.get("error_indices", []))
    from_cache = res.get("from_cache", False)

    # --- THIS IS THE FIX ---
    # Get the sentence power calculated by the server-side check_sentence function
    # It will be None if the sentence was incorrect.
    sentence_power = res.get("sentence_power")
    # --- END OF FIX ---


    # Read priors
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

    # Apply full adventure effects
    try:
        await apply_submission_side_effects(
            db=db,
            user_id=me.id,
            adventure_id=adv.id,
            kc_id=payload.kc_id,
            is_correct=is_correct,
            best_sentence=payload.sentence,
            best_power=sentence_power,  # <-- Pass the server-calculated power
        )

        # Increment attempt counters
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
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Mastery update failed: {ex}")

    # Re-read final values
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

    return SubmissionOut(
        is_correct=is_correct,
        error_indices=error_indices,
        feedback=feedback,
        p_know_adventure=p_adv,
        p_know_overall=p_user,
        from_cache=from_cache,
    )