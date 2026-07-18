"""FastAPI 入口：CORS、路由注册、房间清理任务"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.game_state import cleanup_rooms
from routers import game as game_router
from routers import websocket as ws_router


async def _room_cleaner():
    while True:
        await asyncio.sleep(60)
        cleanup_rooms()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_room_cleaner())
    yield
    task.cancel()


app = FastAPI(title="Skill Gomoku", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router.router)
app.include_router(ws_router.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "skill-gomoku"}