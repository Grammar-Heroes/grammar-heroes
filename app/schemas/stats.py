from typing import List, Optional
from pydantic import BaseModel, Field

# ---------- User KC Mastery ----------
class KCMastery(BaseModel):
    kc_id: int
    p_know: int = Field(0, ge=0, le=100)       # 0..100
    correct: int = 0
    incorrect: int = 0
    best_sentence: Optional[str] = None
    best_sentence_power: Optional[int] = None

class UserKCMasteryListOut(BaseModel):
    mastery: List[KCMastery]

class UserKCMasteryPatchIn(BaseModel):
    mastery: List[KCMastery]

# ---------- Adventure KC Stats ----------
class AdventureKCStatOut(BaseModel):
    kc_id: int
    correct: int = 0
    incorrect: int = 0
    p_know: int = Field(50, ge=0, le=100)
    best_sentence: Optional[str] = None
    best_sentence_power: Optional[int] = None

class AdventureKCStatPatchIn(BaseModel):
    stats: List[AdventureKCStatOut]

# ---------- Adventure Summary ----------
class AdventureSummaryOut(BaseModel):
    status: str
    day_in_epoch_time: int
    highest_floor_cleared: int
    time_spent_seconds: int
    items_collected_json: Optional[str] = None
    node_types_cleared_json: Optional[str] = None
    level: int
    enemy_level: int
    enemies_defeated: int
    best_kc_id: Optional[int] = None
    worst_kc_id: Optional[int] = None
    best_sentence: Optional[str] = None

class AdventureSummaryWithIdOut(AdventureSummaryOut):
    adventure_id: str

class AdventureSummaryPatchIn(BaseModel):
    status: Optional[str] = None
    day_in_epoch_time: Optional[int] = None
    highest_floor_cleared: Optional[int] = None
    time_spent_seconds: Optional[int] = None
    items_collected_json: Optional[str] = None
    node_types_cleared_json: Optional[str] = None
    level: Optional[int] = None
    enemy_level: Optional[int] = None
    enemies_defeated: Optional[int] = None
    best_kc_id: Optional[int] = None
    worst_kc_id: Optional[int] = None
    best_sentence: Optional[str] = None