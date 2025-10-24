import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()

async def get_by_firebase_uid(db: AsyncSession, uid: str) -> User | None:
    res = await db.execute(select(User).where(User.firebase_uid == uid))
    return res.scalar_one_or_none()

async def get_by_display_name(db: AsyncSession, name: str) -> User | None:
    res = await db.execute(select(User).where(User.display_name == name))
    return res.scalar_one_or_none()

async def create_from_firebase(db: AsyncSession, uid: str, email: str | None, name: str | None) -> User:
    user = User(firebase_uid=uid, email=email or f"uid-{uid}@unknown.local")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def set_display_name(db: AsyncSession, user: User, display_name: str) -> User:
    await db.execute(
        update(User).where(User.id == user.id).values(display_name=display_name)
    )
    await db.commit()
    await db.refresh(user)
    return user