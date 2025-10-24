from pydantic import BaseModel

class SubmissionIn(BaseModel):
    adventure_id: str
    kc_id: int
    sentence: str
    is_practice: bool = False

class SubmissionOut(BaseModel):
    is_correct: bool
    error_indices: list[int]
    feedback: list[str]
    p_know_adventure: float
    p_know_overall: float
    from_cache: bool | None = None