from pydantic import BaseModel
from app.schemas.user import UserOut
from app.schemas.adventure import AdventureOut

class HelperData(BaseModel):
    has_adventure: bool
    needs_display_name: bool

class BootstrapOut(BaseModel):
    user: UserOut
    helper: HelperData
    current_adventure: AdventureOut | None