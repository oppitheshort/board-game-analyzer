import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from jwt import InvalidTokenError

from app.config import settings
from app.database import init_db
from app.routers import auth
from app.schemas.board import BoardStateMessage
from app.services.auth_service import decode_access_token
from app.ws.analysis_handler import AnalysisSession
from app.ws.manager import manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Board Game Analyzer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/analysis")
async def ws_analysis(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket, user_id)
    session = AnalysisSession()

    try:
        while True:
            data = await websocket.receive_json()
            try:
                msg = BoardStateMessage(**data)
                result = await session.analyze(msg)
                await manager.send_json(user_id, result.model_dump())
            except Exception as e:
                logger.exception("Analysis error")
                await manager.send_json(user_id, {"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        manager.disconnect(user_id)
