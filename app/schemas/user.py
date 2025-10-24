from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID

class UserOut(BaseModel):
    id: str = Field(..., description="User ID as string")
    email: str
    display_name: Optional[str]
    profile_picture: Optional[str]
    cosmetic_equipped: Optional[str]
    cosmetic_unlocked: List[str] = []
    hero_pass_level: int = 0
    hero_pass_exp: int = 0
    hero_pass_tiers_unlocked: List[int] = []
    achievements_unlocked: List[str] = []
    currency_notes: int = 0
    total_adventures_cleared: int = 0

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: lambda v: str(v)},   # ← active in Pydantic v2
    )


class UserUpdateIn(BaseModel):
    display_name: Optional[str]
    profile_picture: Optional[str]
    cosmetic_equipped: Optional[str]
    cosmetic_unlocked: Optional[List[str]]
    hero_pass_level: Optional[int]
    hero_pass_exp: Optional[int]
    hero_pass_tiers_unlocked: Optional[List[int]]
    achievements_unlocked: Optional[List[str]]
    currency_notes: Optional[int]
    total_adventures_cleared: Optional[int]


class DisplayNameIn(BaseModel):
    display_name: str = Field(..., min_length=3, max_length=16)


class NameAvailabilityOut(BaseModel):
    is_available: bool
    reason: Optional[str] = None