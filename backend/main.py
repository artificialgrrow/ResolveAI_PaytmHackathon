import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path so 'python main.py' works from anywhere
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import init_db
from routes import router
from logger import log
from config import HOST, PORT

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    log.info("[STARTUP] Initializing Paytm ResolveAI Backend...")
    init_db() # Automatically initializes tables and auto-seeds demo data if empty!
    log.info("[STARTUP] Database connection and demo scenarios verified.")
    yield
    log.info("[SHUTDOWN] ResolveAI Backend terminated cleanly.")

app = FastAPI(
    title="Paytm ResolveAI - Autonomous Merchant Incident Resolution Teammate",
    description="Backend API powering multi-agent incident resolution for Paytm merchants.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Vite frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "service": "Paytm ResolveAI",
        "status": "ONLINE",
        "track": "Track 3: Autonomous AI Teammates",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "HEALTHY"}

if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting server on http://{HOST}:{PORT}")
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        app_dir=str(current_dir),
        reload_dirs=[str(current_dir)],
        reload_excludes=[".venv", "*.db", "__pycache__", "paytm_resolve.db*"]
    )

