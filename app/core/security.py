from fastapi import Depends, HTTPException, status, Header
from app.core.firebase import verify_id_token
from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud
from typing import Optional
from app.models.user import User # Import your User model
from firebase_admin import auth # Import firebase_admin.auth

# class DummyUser... (your test code)

# async def get_current_user(
#     authorization: Optional[str] = Header(None), 
#     db: AsyncSession = Depends(get_db)
# ) -> User: # Explicitly type the return as your User model
    
#     if not authorization:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
    
#     token = authorization.split(" ", 1)[1]
    
#     # 1. Verify token
#     # This now handles revoked tokens automatically
#     decoded = verify_id_token(token)
    
#     uid = decoded.get("uid")
#     # This is the key: a Unix timestamp of when the token was created
#     token_auth_time = decoded.get("auth_time")
    
#     if not uid or not token_auth_time:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
#     # 2. Get or Create User
#     user = await crud.user.get_by_firebase_uid(db, uid)
    
#     if not user:
#         # --- NEW USER (FIRST LOGIN) ---
#         # Call your updated create function
#         user = await crud.user.create_from_firebase(
#             db, 
#             uid, 
#             decoded.get("email"), 
#             decoded.get("name"),
#             token_auth_time  # Pass the auth_time
#         )
#         # This user is new, their session is valid by default.
#         return user

#     # --- EXISTING USER: PERFORM SESSION CHECK ---
    
#     db_auth_time = user.active_session_auth_time
    
#     if db_auth_time is None:
#         # User exists, but from before you deployed this feature.
#         # "Upgrade" them to the new system.
#         user.active_session_auth_time = token_auth_time
#         await db.commit()
#         await db.refresh(user)
#         return user

#     if token_auth_time > db_auth_time:
#         # --- NEW LOGIN DETECTED ---
#         # "Last Login Wins"
#         # This token is from a NEWER login than the one in our DB.
        
#         # 1. Update the DB to this new timestamp
#         user.active_session_auth_time = token_auth_time
        
#         # 2. (RECOMMENDED) Revoke all other sessions for this user
#         # This is a synchronous (blocking) call, but it's crucial.
#         try:
#             auth.revoke_refresh_tokens(uid)
#             print(f"Revoked all refresh tokens for user {uid} due to new login.")
#         except Exception as e:
#             # Log this error, but don't fail the request
#             print(f"ERROR: Could not revoke tokens for {uid}: {e}")
        
#         await db.commit()
#         await db.refresh(user)
        
#         # This new session is now the only valid one
#         return user

#     elif token_auth_time == db_auth_time:
#         # --- VALID, EXISTING SESSION ---
#         # The token's auth_time matches the DB. This is the normal
#         # case for a user making many requests from one device.
#         return user

#     elif token_auth_time < db_auth_time:
#         # --- STALE SESSION DETECTED ---
#         # This token is OLD. A newer login (with a > auth_time)
#         # has already been recorded. This session is terminated.
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="SESSION_TERMINATED",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
        
#     # Failsafe, though one of the above should always catch
#     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

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
        user = await crud.user.create_from_firebase(
            db, 
            uid, 
            decoded.get("email"), 
            decoded.get("name"),
            token_auth_time
        )
        return user

    # --- EXISTING USER: PERFORM SESSION CHECK ---
    
    db_auth_time = user.active_session_auth_time
    
    if db_auth_time is None:
        # User exists, but from before you deployed this feature.
        user.active_session_auth_time = token_auth_time
        await db.commit()
        await db.refresh(user)
        return user

    if token_auth_time > db_auth_time:
        # --- NEW LOGIN DETECTED ---
        # Just update the DB time. This is the only action needed.
        user.active_session_auth_time = token_auth_time
        await db.commit()
        await db.refresh(user)
        return user

    elif token_auth_time == db_auth_time:
        # --- VALID, EXISTING SESSION ---
        return user

    elif token_auth_time < db_auth_time:
        # --- STALE SESSION DETECTED ---
        # This correctly kicks the OLD device (Device 1).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_TERMINATED",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")