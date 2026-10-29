from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import get_settings
from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.api.routes.scans import router as scans_router
from app.core.exceptions import register_exception_handlers
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):

    settings = get_settings()
    app.state.settings = settings

    yield



setting = get_settings()


app = FastAPI(
    title=setting.app_name,
    debug=False,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://crop-health-chi.vercel.app/scanner",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(
    scans_router,
    prefix=setting.api_v2_prefix
)

@app.get("/", tags=["Genral"])
async def root():
    return {
        "message": "Crop Health AI API",
        "status": "running",
    }


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    return {
        "status": "alive"
    }

@app.get("/health/ready", tags=["Health"])
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            }
        )


