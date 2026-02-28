from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import repo
from .config import settings

app = FastAPI(
    title="RepoDocAI",
    description="AI-powered repository documentation generator with AMD GPU acceleration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repo.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "description": "AI-powered repository documentation generator",
        "version": "1.0.0",
        "amd_powered": True,
    }
