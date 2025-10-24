from pydantic import BaseModel, Field

class AdventureOut(BaseModel):
    id: str
    user_id: str
    seed: str
    state: str
    current_node_id: str | None
    current_node_kc: int | None
    cleared_nodes: list[str]
    items_collected: list[str]
    node_name: str | None
    current_floor: int
    level: int
    add_writing_level: int
    add_defense_level: int
    enemy_level: int
    add_enemy_writing_level: int
    add_enemy_defense_level: int
    is_practice: bool
    enemies_defeated: int = 0
    reward_hero_pass_exp: int = 0
    reward_notes: int = 0
    node_types_cleared: list[int] = []
    correct_submissions: int = 0
    incorrect_submissions: int = 0
    

class AdventureStartIn(BaseModel):
    seed: str
    is_practice: bool = False

class AdventureProgressIn(BaseModel):
    current_node_id: str | None = None
    current_node_kc: int | None = None
    cleared_nodes: list[str] | None = None
    items_collected: list[str] | None = None
    node_name: str | None = None
    current_floor: int | None = None
    level: int | None = None
    add_writing_level: int | None = None
    add_defense_level: int | None = None
    enemy_level: int | None = None
    add_enemy_writing_level: int | None = None
    add_enemy_defense_level: int | None = None
    enemies_defeated: int | None = None
    reward_hero_pass_exp: int | None = None
    reward_notes: int | None = None
    node_types_cleared: list[int] | None = None
    correct_submissions: int | None = None
    incorrect_submissions: int | None = None

class AdventureFinishIn(BaseModel):
    status: str  # Success or Failed
    day_in_epoch_time: int
    highest_floor_cleared: int
    time_spent_seconds: int
    items_collected: list[str] = []
    node_types_cleared: list[int] = []
    level: int
    enemy_level: int
    enemies_defeated: int
    best_sentence: str | None = None