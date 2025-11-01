from fastapi import Depends, HTTPException, status, Header
from app.core.firebase import verify_id_token
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud  
from typing import Optional

class DummyUser:
    id = 1
    email = "test@example.com"

async def get_current_user(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    
    token = authorization.split(" ", 1)[1]
    decoded = verify_id_token(token)
    uid = decoded.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await crud.user.get_by_firebase_uid(db, uid)
    if not user:
        # create new user
        user = await crud.user.create_from_firebase(db, uid, decoded.get("email"), decoded.get("name"))
    return user
    # return DummyUser()

# NOTE : The code is commented for testing purposes.