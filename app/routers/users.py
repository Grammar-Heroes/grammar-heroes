from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_current_user
from app.core.db import get_db
from app.schemas.user import DisplayNameIn, UserOut, NameAvailabilityOut, UserUpdateIn
from app.utils.validators import valid_display_name
from app.crud import user as user_crud
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def me_route(me=Depends(get_current_user)):
    return {
        "id": str(me.id),
        "email": me.email,
        "display_name": me.display_name,
        "profile_picture": me.profile_picture,
        "cosmetic_equipped": me.cosmetic_equipped,
        "cosmetic_unlocked": list(me.cosmetic_unlocked or []),
        "hero_pass_level": me.hero_pass_level,
        "hero_pass_exp": me.hero_pass_exp,
        "hero_pass_tiers_unlocked": list(me.hero_pass_tiers_unlocked or []),
        "achievements_unlocked": list(me.achievements_unlocked or []),
        "currency_notes": me.currency_notes,
        "total_adventures_cleared": me.total_adventures_cleared,

        # New stats
        "recorded_items": list(me.recorded_items or []),
        "total_parry_counts": me.total_parry_counts,
        "total_enemies_defeated": me.total_enemies_defeated,
        "total_damage_received": me.total_damage_received,
        "total_damage_dealt": me.total_damage_dealt,
    }

@router.get("/display-name/availability", response_model=NameAvailabilityOut)
async def display_name_availability(name: str, db: AsyncSession = Depends(get_db)):
    if not valid_display_name(name):
        return NameAvailabilityOut(is_available=False, reason="invalid")
    existing = await user_crud.get_by_display_name(db, name)
    if existing:
        return NameAvailabilityOut(is_available=False, reason="taken")
    return NameAvailabilityOut(is_available=True, reason=None)

@router.patch("/display-name", response_model=UserOut)
async def set_display_name(
    payload: DisplayNameIn,
    me=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if me.display_name is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Display name already set")
    if not valid_display_name(payload.display_name):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid display name")

    existing = await user_crud.get_by_display_name(db, payload.display_name)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Display name taken")

    me = await user_crud.set_display_name(db, me, payload.display_name)
    return await me_route(me)  # type: ignore

@router.patch("/me", response_model=UserOut)
async def update_user_me(
    payload: UserUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_fields = [
        "display_name",
        "profile_picture",
        "cosmetic_equipped",
        "cosmetic_unlocked",
        "hero_pass_level",
        "hero_pass_exp",
        "hero_pass_tiers_unlocked",
        "achievements_unlocked",
        "currency_notes",
        "total_adventures_cleared",
        "recorded_items",
        "total_parry_counts",
        "total_enemies_defeated",
        "total_damage_received",
        "total_damage_dealt",
    ]
    for field in update_fields:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "profile_picture": user.profile_picture,
        "cosmetic_equipped": user.cosmetic_equipped,
        "cosmetic_unlocked": list(user.cosmetic_unlocked or []),
        "hero_pass_level": user.hero_pass_level,
        "hero_pass_exp": user.hero_pass_exp,
        "hero_pass_tiers_unlocked": list(user.hero_pass_tiers_unlocked or []),
        "achievements_unlocked": list(user.achievements_unlocked or []),
        "currency_notes": user.currency_notes,
        "total_adventures_cleared": user.total_adventures_cleared,
        "recorded_items": list(user.recorded_items or []),
        "total_parry_counts": user.total_parry_counts,
        "total_enemies_defeated": user.total_enemies_defeated,
        "total_damage_received": user.total_damage_received,
        "total_damage_dealt": user.total_damage_dealt,
    }