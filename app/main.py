from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, bootstrap, adventures, submissions
from app.routers import stats as stats_router
from app.core.db import engine, Base

app = FastAPI(title="Grammar Heroes API", version="1.0.0")

# CORS: adjust for Unity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # lock down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(bootstrap.router, prefix="/bootstrap", tags=["bootstrap"])
app.include_router(adventures.router, prefix="/adventures", tags=["adventures"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
app.include_router(stats_router.router, prefix="/stats", tags=["stats"])

@app.get("/")
async def root():
    return {"ok": True, "service": "grammar-heroes", "version": "1.0.0"}