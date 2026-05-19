from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import init_db

app = FastAPI(title="需求池管理系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


# 挂载静态文件（挂载到 /app/static 避免拦截根路径）
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/app/static", StaticFiles(directory=static_path), name="static")


from app.routers import requirements, reviews, import_csv, stats, qa

app.include_router(stats.router, prefix="/api", tags=["统计"])
app.include_router(requirements.router, prefix="/api", tags=["需求"])
app.include_router(reviews.router, prefix="/api", tags=["评审"])
app.include_router(import_csv.router, prefix="/api", tags=["导入"])
app.include_router(qa.router, prefix="/api", tags=["智能问答"])


@app.get("/", response_class=HTMLResponse)
def root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return {"message": "需求池管理系统 API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}