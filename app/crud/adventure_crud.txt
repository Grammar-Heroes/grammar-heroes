import uuid
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.adventure import Adventure
from app.models.enums import AdventureState

async def get_active_for_user(db: AsyncSession, user_id: uuid.UUID):
    res = await db.execute(
        select(Adventure).where(
            Adventure.user_id == user_id,
            Adventure.state == AdventureState.IN_PROGRESS.value,
        )
    )
    return res.scalar_one_or_none()

async def get_by_id(db: AsyncSession, adv_id: uuid.UUID):
    res = await db.execute(select(Adventure).where(Adventure.id == adv_id))
    return res.scalar_one_or_none()

async def get_by_id_and_user(db: AsyncSession, adv_id: uuid.UUID, user_id: uuid.UUID):
    res = await db.execute(
        select(Adventure).where(Adventure.id == adv_id, Adventure.user_id == user_id)
    )
    return res.scalar_one_or_none()

async def create(db: AsyncSession, user_id: uuid.UUID, is_practice: bool, seed: str):
    adv = Adventure(user_id=user_id, is_practice=is_practice, seed=seed)
    db.add(adv)
    await db.commit()
    await db.refresh(adv)
    return adv

async def update_partial(db: AsyncSession, adv: Adventure, data: dict):
    await db.execute(update(Adventure).where(Adventure.id == adv.id).values(**data))
    await db.commit()
    await db.refresh(adv)
    return adv

async def finish(db: AsyncSession, adv: Adventure, status: str):
    await db.execute(
        update(Adventure)
        .where(Adventure.id == adv.id)
        .values(state=status, finished_at=func.now())
    )
    await db.commit()
    await db.refresh(adv)
    return adv

async def abandon_active_for_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Treat 'abandoned' as FAILED."""
    res = await db.execute(
        update(Adventure)
        .where(Adventure.user_id == user_id, Adventure.state == AdventureState.IN_PROGRESS.value)
        .values(state=AdventureState.FAILED.value, finished_at=func.now())
        .returning(Adventure.id)
    )
    await db.commit()
    return len(res.fetchall())