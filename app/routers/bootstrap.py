# # app/routers/bootstrap.py
# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.core.security import get_current_user
# from app.core.db import get_db
# from app.schemas.bootstrap import BootstrapOut, HelperData
# from app.schemas.user import UserOut
# from app.schemas.adventure import AdventureOut
# from app.crud import adventure as adv_crud

# router = APIRouter()


# def _ival(v, default=0) -> int:
#     return int(v) if v is not None else default


# @router.get("", response_model=BootstrapOut)
# async def bootstrap(me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
#     adv = await adv_crud.get_active_for_user(db, me.id)

#     helper = HelperData(
#         has_adventure=adv is not None,
#         needs_display_name=me.display_name is None,
#     )

#     user_out = UserOut(
#         id=str(me.id),
#         email=me.email,
#         display_name=me.display_name,
#         profile_picture=me.profile_picture,
#         cosmetic_equipped=me.cosmetic_equipped,
#         cosmetic_unlocked=list(me.cosmetic_unlocked or []),
#         hero_pass_level=_ival(getattr(me, "hero_pass_level", None), 0),
#         hero_pass_exp=_ival(getattr(me, "hero_pass_exp", None), 0),
#         hero_pass_tiers_unlocked=list(me.hero_pass_tiers_unlocked or []),
#         achievements_unlocked=list(me.achievements_unlocked or []),
#         currency_notes=_ival(getattr(me, "currency_notes", None), 0),
#         total_adventures_cleared=_ival(
#             getattr(me, "total_adventures_cleared", None), 0
#         ),
#         # New fields
#         recorded_items=list(me.recorded_items or []),
#         total_parry_counts=_ival(getattr(me, "total_parry_counts", None), 0),
#         total_enemies_defeated=_ival(getattr(me, "total_enemies_defeated", None), 0),
#         total_damage_received=_ival(getattr(me, "total_damage_received", None), 0),
#         total_damage_dealt=_ival(getattr(me, "total_damage_dealt", None), 0),
        
#         # New fields 2
#         powerpedia_unlocked=list(me.powerpedia_unlocked or []),  # <-- Added this line
#         tutorials_recorded=list(me.tutorials_recorded or []),  # <-- Added this line
#     )

#     adv_out = None
#     if adv:
#         adv_out = AdventureOut(
#             id=str(adv.id),
#             user_id=str(adv.user_id),
#             seed=(adv.seed or ""),
#             state=adv.state or "in_progress",
#             current_node_id=adv.current_node_id or "",
#             current_node_kc=int(adv.current_node_kc or 1),
#             cleared_nodes=list(adv.cleared_nodes or []),
#             items_collected=list(adv.items_collected or []),
#             node_name=adv.node_name or "",
#             current_floor=int(adv.current_floor or 1),
#             level=int(adv.level or 1),
#             add_writing_level=int(adv.add_writing_level or 0),
#             add_defense_level=int(adv.add_defense_level or 0),
#             enemy_level=int(adv.enemy_level or 1),
#             add_enemy_writing_level=int(adv.add_enemy_writing_level or 0),
#             add_enemy_defense_level=int(adv.add_enemy_defense_level or 0),
#             is_practice=bool(getattr(adv, "is_practice", False)),
#             enemies_defeated=_ival(getattr(adv, "enemies_defeated", None), 0),
#             reward_hero_pass_exp=_ival(
#                 getattr(adv, "reward_hero_pass_exp", None), 0
#             ),
#             reward_notes=_ival(getattr(adv, "reward_notes", None), 0),
#             node_types_cleared=list(adv.node_types_cleared or []),
#             correct_submissions=_ival(getattr(adv, "correct_submissions", None), 0),
#             incorrect_submissions=_ival(
#                 getattr(adv, "incorrect_submissions", None), 0
#             ),
#             # New fields
#             total_damage_dealt=_ival(getattr(adv, "total_damage_dealt", None), 0),
#             total_damage_received=_ival(
#                 getattr(adv, "total_damage_received", None), 0
#             ),
#         )

#     return {
#         "user": user_out,
#         "helper": helper,
#         "current_adventure": adv_out,
#     }

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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


def _ival(v, default=0): return int(v) if v is not None else default


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
            items_collected=summary.items_collected_json.split(",") if summary.items_collected_json else [],
            node_types_cleared=[int(x) for x in summary.node_types_cleared_json.split(",") if x]
            if summary.node_types_cleared_json else [],
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
