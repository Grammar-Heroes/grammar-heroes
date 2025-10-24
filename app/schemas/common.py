from pydantic import BaseModel, Field

class Msg(BaseModel):
    message: str

class IdModel(BaseModel):
    id: str = Field(..., description="UUID string")