from pydantic import BaseModel


class AdventureSummaryOut(BaseModel):
    status: str
    day_in_epoch_time: int
    highest_floor_cleared: int
    time_spent_seconds: int
    items_collected: list[str] | None = None
    node_types_cleared: list[int] | None = None
    level: int
    enemy_level: int
    enemies_defeated: int
    best_kc_id: int | None = None
    best_sentence: str | None = None
    total_damage_dealt: int | None = None
    total_damage_received: int | None = None

    class Config:
        orm_mode = True
