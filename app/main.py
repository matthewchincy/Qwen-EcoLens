from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import webhooks
from app.db.session import engine
from app.db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables (for MVP simplicity, usually use Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title="Qwen-EcoLens", lifespan=lifespan)

app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])

@app.get("/")
def health_check():
    return {"status": "running", "service": "Qwen-EcoLens"}
