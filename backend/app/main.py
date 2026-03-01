import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

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

# ── Static frontend (production) ─────────────────
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/")
async def root(request: Request):
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {
        "name": settings.APP_NAME,
        "description": "AI-powered repository documentation generator",
        "version": "1.0.0",
        "amd_powered": True,
    }


# Mount static assets if they exist (CSS, JS, images)
if STATIC_DIR.exists():
    # Mount _next and other static dirs
    next_dir = STATIC_DIR / "_next"
    if next_dir.exists():
        app.mount("/_next", StaticFiles(directory=str(next_dir)), name="next_static")

    # Static assets
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


# SPA catch-all — serve generate page for /generate?taskId=... (must be LAST)
@app.get("/generate")
async def spa_generate(request: Request):
    """Serve the static /generate page (uses query params for taskId)."""
    page = STATIC_DIR / "generate" / "index.html"
    if page.exists():
        return FileResponse(page)
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse("<h1>Page not found</h1>", status_code=404)
