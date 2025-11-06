from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str | None = None
    DATABASE_URL_SYNC: str | None = None
    REDIS_URL: str | None = None          
    FIREBASE_CREDENTIALS: str | None = None
    T5_API_KEY: str | None = None
    T5_API_URL: str | None = None
    DEBUG: bool = False
    GEMINI_API_KEY: str | None = None
    

    class Config:
        env_file = ".env"

settings = Settings()