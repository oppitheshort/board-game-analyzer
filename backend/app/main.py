import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError

from app.config import settings
from app.database import init_db
from app.routers import auth
from app.schemas.board import BoardStateMessage
from app.services.auth_service import decode_access_token
from app.ws.analysis_handler import AnalysisSession
from app.ws.manager import manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-IP)
# ---------------------------------------------------------------------------
class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window
        # Prune old entries
        self._hits[key] = [t for t in self._hits[key] if t > window_start]
        if len(self._hits[key]) >= self.max_requests:
            return False
        self._hits[key].append(now)
        return True


# 10 auth attempts per minute per IP, 5 registrations per minute per IP
auth_limiter = RateLimiter(max_requests=10, window_seconds=60)
register_limiter = RateLimiter(max_requests=5, window_seconds=60)


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# Disable interactive docs in production
docs_kwargs = {}
if settings.environment == "production":
    docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(title="Board Game Analyzer", version="0.1.0", lifespan=lifespan, **docs_kwargs)

# CORS: only allow BGA origins and our own domain — not the entire internet
allowed_origins = [
    "https://boardgamearena.com",
    "https://en.boardgamearena.com",
    "http://boardgamearena.com",
    "http://en.boardgamearena.com",
    "http://localhost:5173",
    "http://localhost:3000",
]
# Add any custom origins from the config
for origin in settings.cors_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(auth.router)


# ---------------------------------------------------------------------------
# Rate-limit middleware for auth endpoints
# ---------------------------------------------------------------------------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    client_ip = request.headers.get("x-real-ip", request.client.host if request.client else "unknown")

    if path == "/api/auth/login" and request.method == "POST":
        if not auth_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many login attempts. Please try again later."},
            )

    if path == "/api/auth/register" and request.method == "POST":
        if not register_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many registration attempts. Please try again later."},
            )

    return await call_next(request)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket analysis endpoint
# ---------------------------------------------------------------------------
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
            raw = await websocket.receive_text()

            # Enforce message size limit
            if len(raw) > settings.ws_max_message_bytes:
                await manager.send_json(user_id, {"type": "error", "message": "Message too large"})
                continue

            try:
                import json

                data = json.loads(raw)
                msg = BoardStateMessage(**data)
                result = await session.analyze(msg)
                await manager.send_json(user_id, result.model_dump())
            except Exception as e:
                logger.exception("Analysis error")
                await manager.send_json(user_id, {"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        manager.disconnect(user_id)
