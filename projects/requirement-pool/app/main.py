from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.database import Base, engine
from app import models  # noqa: F401
from app.routers import requirements as requirements_router
from app.routers import import_csv as import_csv_router
from app.routers import reviews as reviews_router
from app.routers import stats as stats_router
from app.routers import export as export_router
from app.routers import ai as ai_router

app = FastAPI(title="需求池管理系统", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(stats_router.router, prefix="/api", tags=["看板"])
app.include_router(requirements_router.router, prefix="/api", tags=["需求"])
app.include_router(import_csv_router.router, prefix="/api", tags=["导入"])
app.include_router(export_router.router, prefix="/api", tags=["导出"])
app.include_router(reviews_router.router, prefix="/api", tags=["评审"])
app.include_router(ai_router.router, prefix="/api", tags=["AI分析"])

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}

