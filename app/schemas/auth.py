from pydantic import BaseModel

class SyncOut(BaseModel):
    user_id: str
    email: str
    display_name: str | None
    first_time_login: bool