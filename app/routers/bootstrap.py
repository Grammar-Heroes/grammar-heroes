# app/routers/bootstrap.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.core.security import get_current_user
from app.core.db import get_db
from app.schemas.bootstrap import BootstrapOut, HelperData
from app.schemas.user import UserOut
from app.schemas.adventure import AdventureOut
from app.schemas.summary import AdventureSummaryOut
from app.models.stats import AdventureSummary
from app.models.adventure import Adventure
from app.crud import adventure as adv_crud

router = APIRouter()


def _ival(v, default: int = 0) -> int:
    return int(v) if v is not None else default


def _parse_items_collected(raw: str | None) -> list[str]:
    """
    Accepts either:
      - JSON array string, e.g. ["item_any_branchblossom"]
      - Comma-separated string, e.g. item_any_branchblossom,item_other
    Returns a list of strings.
    """
    if not raw:
        return []

    s = raw.strip()
    # JSON array form
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            # fall through to loose parsing
            pass

    # Fallback: comma-separated
    parts = []
    for part in s.split(","):
        p = part.strip().strip("[]\"")
        if p:
            parts.append(p)
    return parts


def _parse_node_types(raw: str | None) -> list[int]:
    """
    Accepts either:
      - JSON array string, e.g. [0,0,0]
      - Comma-separated string, e.g. 0,0,0
    Returns a list[int].
    """
    if not raw:
        return []

    s = raw.strip()
    # JSON array form
    if s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return [int(x) for x in data if x is not None]
        except Exception:
            # fall through to loose parsing
            pass

    # Fallback: tolerant comma-split with bracket stripping
    result: list[int] = []
    for part in s.split(","):
        p = part.strip().strip("[]")
        if not p:
            continue
        try:
            result.append(int(p))
        except ValueError:
            # ignore bad tokens instead of blowing up bootstrap
            continue
    return result


@router.get("", response_model=BootstrapOut)
async def bootstrap(me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    adv = await adv_crud.get_active_for_user(db, me.id)

    helper = HelperData(
        has_adventure=adv is not None,
        needs_display_name=me.display_name is None,
    )

    user_out = UserOut(
        id=str(me.id),
        email=me.email,
        display_name=me.display_name,
        profile_picture=me.profile_picture,
        cosmetic_equipped=me.cosmetic_equipped,
        cosmetic_unlocked=list(me.cosmetic_unlocked or []),
        hero_pass_level=_ival(getattr(me, "hero_pass_level", None), 0),
        hero_pass_exp=_ival(getattr(me, "hero_pass_exp", None), 0),
        hero_pass_tiers_unlocked=list(me.hero_pass_tiers_unlocked or []),
        achievements_unlocked=list(me.achievements_unlocked or []),
        currency_notes=_ival(getattr(me, "currency_notes", None), 0),
        total_adventures_cleared=_ival(getattr(me, "total_adventures_cleared", None), 0),
        recorded_items=list(me.recorded_items or []),
        total_parry_counts=_ival(getattr(me, "total_parry_counts", None), 0),
        total_enemies_defeated=_ival(getattr(me, "total_enemies_defeated", None), 0),
        total_damage_received=_ival(getattr(me, "total_damage_received", None), 0),
        total_damage_dealt=_ival(getattr(me, "total_damage_dealt", None), 0),
        powerpedia_unlocked=list(me.powerpedia_unlocked or []),
        tutorials_recorded=list(me.tutorials_recorded or []),
    )

    adv_out = None
    adventure_history: list[AdventureSummaryOut] = []

    if adv:
        # Uses your AdventureOut.from_orm mapping so it stays aligned with Unity DTO
        adv_out = AdventureOut.from_orm(adv)

    # ─── FETCH ALL ADVENTURE SUMMARIES FOR THIS USER ───
    results = await db.scalars(
        select(AdventureSummary)
        .join(Adventure, AdventureSummary.adventure_id == Adventure.id)
        .where(Adventure.user_id == me.id)
        .order_by(AdventureSummary.day_in_epoch_time.desc())
    )

    for summary in results.all():
        history_entry = AdventureSummaryOut(
            status=summary.status,
            day_in_epoch_time=_ival(summary.day_in_epoch_time, 0),
            highest_floor_cleared=_ival(summary.highest_floor_cleared, 0),
            time_spent_seconds=_ival(summary.time_spent_seconds, 0),
            items_collected=_parse_items_collected(summary.items_collected_json),
            node_types_cleared=_parse_node_types(summary.node_types_cleared_json),
            level=_ival(summary.level, 0),
            enemy_level=_ival(summary.enemy_level, 0),
            enemies_defeated=_ival(summary.enemies_defeated, 0),
            best_kc_id=summary.best_kc_id,
            best_sentence=summary.best_sentence,
            total_damage_dealt=_ival(summary.total_damage_dealt, 0),
            total_damage_received=_ival(summary.total_damage_received, 0),
        )
        adventure_history.append(history_entry)

    return {
        "user": user_out,
        "helper": helper,
        "current_adventure": adv_out,
        "adventure_history": adventure_history,
    }
