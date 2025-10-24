# app/services/mastery.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stats import UserKCMastery, AdventureKCStat
from app.services import bkt_service as bkt

async def apply_submission_side_effects(
    db: AsyncSession,
    user_id,
    adventure_id,
    kc_id: int,
    is_correct: bool,
    best_sentence: str | None = None,
    best_power: int | None = None,
    slip: float = 0.1,
    guess: float = 0.2,
    transit: float = 0.15,
) -> None:
    # ----- USER LEVEL -----
    res = await db.execute(
        select(UserKCMastery).where(
            UserKCMastery.user_id == user_id,
            UserKCMastery.kc_id == kc_id,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        row = UserKCMastery(
            user_id=user_id,
            kc_id=kc_id,
            p_know=50,
            correct=1 if is_correct else 0,
            incorrect=0 if is_correct else 1,
        )
        db.add(row)
    else:
        prior = (row.p_know or 0) / 100.0
        updated = bkt.update_pknow(prior, is_correct, slip=slip, guess=guess, transit=transit)
        row.p_know = int(round(updated * 100))
        if is_correct: row.correct += 1
        else:          row.incorrect += 1

    # best sentence update
    if best_power is not None and (row.best_sentence_power or -1) < int(best_power):
        row.best_sentence_power = int(best_power)
        if best_sentence:
            row.best_sentence = best_sentence

    # ensure INSERTs are staged before we read from them
    await db.flush()

    # ----- ADVENTURE LEVEL -----
    res = await db.execute(
        select(AdventureKCStat).where(
            AdventureKCStat.adventure_id == adventure_id,
            AdventureKCStat.kc_id == kc_id,
        )
    )
    arow = res.scalar_one_or_none()
    if arow is None:
        arow = AdventureKCStat(
            adventure_id=adventure_id,
            kc_id=kc_id,
            p_know=row.p_know,  # start from user-level prior
            correct=1 if is_correct else 0,
            incorrect=0 if is_correct else 1,
        )
        db.add(arow)
    else:
        aprior = (arow.p_know or 0) / 100.0
        anew = bkt.update_pknow(aprior, is_correct, slip=slip, guess=guess, transit=transit)
        arow.p_know = int(round(anew * 100))
        if is_correct: arow.correct += 1
        else:          arow.incorrect += 1

    await db.commit()