from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.core.db import get_db
from app.schemas.auth import SyncOut

router = APIRouter()

@router.post("/sync", response_model=SyncOut)
async def sync(me=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    first_time = me.display_name is None
    return {
        "user_id": str(me.id),
        "email": me.email,
        "display_name": me.display_name,
        "first_time_login": first_time,
    }