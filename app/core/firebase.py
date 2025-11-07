import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
from fastapi import HTTPException, status

def init_firebase():
    if not firebase_admin._apps:
        if not settings.FIREBASE_CREDENTIALS:
            raise RuntimeError("FIREBASE_CREDENTIALS is not set in env")
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)

def verify_id_token(id_token: str) -> dict:
    init_firebase()
    try:
        # --- MODIFICATION ---
        # Add check_revoked=True
        decoded = auth.verify_id_token(id_token, check_revoked=True)
        # --- END MODIFICATION ---
        
        print("Decoded token:", decoded)
        return decoded
        
    # --- MODIFICATION ---
    # Catch this specific error
    except auth.RevokedIdTokenError as exc:
        print("Token was revoked:", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_TERMINATED", # Send specific "kicked" error
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    # --- END MODIFICATION ---
        
    except Exception as exc:  
        print("Token verification failed:", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Firebase token"
        ) from exc