import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stats import AdventureKCStat, AdventureSummary, UserKCMastery

async def get_or_create_adv_kc(db: AsyncSession, adventure_id: uuid.UUID, kc_id: int) -> AdventureKCStat:
    res = await db.execute(
        select(AdventureKCStat).where(
            AdventureKCStat.adventure_id == adventure_id,
            AdventureKCStat.kc_id == kc_id,
        )
    )
    row = res.scalar_one_or_none()
    if row:
        return row
    # initialize to 50 (neutral). If you prefer to seed from user mastery, do a quick lookup here.
    row = AdventureKCStat(adventure_id=adventure_id, kc_id=kc_id, p_know=50)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row

async def upsert_user_mastery(db: AsyncSession, user_id: uuid.UUID, kc_id: int) -> UserKCMastery:
    res = await db.execute(
        select(UserKCMastery).where(
            UserKCMastery.user_id == user_id,
            UserKCMastery.kc_id == kc_id,
        )
    )
    row = res.scalar_one_or_none()
    if row:
        return row
    row = UserKCMastery(user_id=user_id, kc_id=kc_id)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row

async def create_summary(db: AsyncSession, summary: AdventureSummary) -> AdventureSummary:
    db.add(summary)
    await db.commit()
    await db.refresh(summary)
    return summary

    # When the an adventure is done, the screenshot shows.
    # When I click "Claim Rewards" -> It triggers FloorLoadingHandler.ClaimFinalRewards()
    # Which then calls the Coroutine AdventureMenuClear from LoadingHandler
    # Which is assigned as the IEnumerator AdventureClearLoadMenu()
    # Just follow whatever it LoadingHandler and FloorLoadingHandler takes you.
    # The goal is store this AdventureHistory in the database