from fastapi import Depends, HTTPException, status, Header
from app.core.firebase import verify_id_token
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError  # <--- IMPORT THIS
from app import crud
from typing import Optional
from app.models.user import User
from firebase_admin import auth

async def get_current_user(
    authorization: Optional[str] = Header(None), 
    db: AsyncSession = Depends(get_db)
) -> User:
    
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    
    token = authorization.split(" ", 1)[1]
    
    # 1. Verify token
    decoded = verify_id_token(token)
    
    uid = decoded.get("uid")
    token_auth_time = decoded.get("auth_time")
    
    if not uid or not token_auth_time:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    # 2. Get or Create User
    user = await crud.user.get_by_firebase_uid(db, uid)
    
    if not user:
        # --- NEW USER (FIRST LOGIN) ---
        try:
            user = await crud.user.create_from_firebase(
                db, 
                uid, 
                decoded.get("email"), 
                decoded.get("name"),
                token_auth_time
            )
        except IntegrityError:
            # Race condition: Another request created the user milliseconds ago.
            # Rollback the failed transaction to clean up the session.
            await db.rollback()
            
            # Fetch the user that was just created by the other thread
            user = await crud.user.get_by_firebase_uid(db, uid)
            
            if not user:
                # If it's still missing, something is actually wrong.
                raise HTTPException(status_code=500, detail="User creation failed unexpectedly")
        
        return user

    # --- EXISTING USER: PERFORM SESSION CHECK ---
    
    db_auth_time = user.active_session_auth_time
    
    if db_auth_time is None:
        user.active_session_auth_time = token_auth_time
        await db.commit()
        await db.refresh(user)
        return user

    if token_auth_time > db_auth_time:
        user.active_session_auth_time = token_auth_time
        await db.commit()
        await db.refresh(user)
        return user

    elif token_auth_time == db_auth_time:
        return user

    elif token_auth_time < db_auth_time:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_TERMINATED",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")