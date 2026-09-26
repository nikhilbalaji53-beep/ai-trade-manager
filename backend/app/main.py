import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.api.routes import alerts, market, portfolio, records, strategies, system, trades, analytics
from app.api.routes.v1_market import v1_router
from app.api.routes.v1_trades import v1_trades_router
from app.api.routes.v1_positions import v1_pos_router
from app.api.routes.v1_markets import markets_router
from app.api.routes.v1_ai import ai_router
from app.api.routes.v1_paper import paper_router
from app.api.routes.v1_instruments import instruments_router
from app.api.routes.v1_auth import auth_router
from app.api.routes.v1_crypto import crypto_router
from app.config import get_settings
from app.services.market_data.market_data_manager import get_market_data_manager
from app.services.market_data.websocket_manager import get_websocket_manager
from app.services.trade_manager import TradeManager
from app.database import get_store
from app.services.decision_engine import generate_ai_signals

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    manager = get_market_data_manager()
    manager.initialize()
    bg_task = asyncio.create_task(manager.start_background_stream())
    logger.info("TradePilot market data manager stream initialized.")
    yield
    # Shutdown
    manager.stop_background_stream()
    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass
    logger.info("TradePilot market data manager stream terminated.")


app = FastAPI(
    title="TradePilot AI — Intelligent Real-Time Trading",
    version="2.5.0",
    description="TradePilot AI — 'Monitor. Predict. Learn. Protect. Trade.' Complete AI-Assisted Market Analysis & Paper Trading Platform",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else "/api/v1/docs",
    redoc_url="/redoc" if not settings.is_production else "/api/v1/redoc",
)

# Production GZip Payload Compression
app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)

# Production Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# Production CORS Policy configuration for frontend communication
allowed_origins = settings.cors_origin_list
has_wildcard = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    # Regex covers:
    #   • localhost / 127.0.0.1 on any port  (development)
    #   • any *.onrender.com subdomain       (production — frontend & backend on Render)
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
        r"|https://[a-zA-Z0-9\-]+\.onrender\.com"
    ) if not has_wildcard else None,
    allow_credentials=not has_wildcard,  # Browser CORS spec mandates credentials=False when origins='*'
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "path": request.url.path,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "path": request.url.path,
        },
    )

# V1 API Routes
app.include_router(v1_router, prefix="/api")
app.include_router(markets_router, prefix="/api")
app.include_router(instruments_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(paper_router, prefix="/api")
app.include_router(v1_trades_router, prefix="/api")
app.include_router(v1_pos_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(crypto_router, prefix="/api")

# Core Subsystem Routes
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(portfolio.router, prefix=settings.api_prefix)
app.include_router(trades.router, prefix=settings.api_prefix)
app.include_router(strategies.router, prefix=settings.api_prefix)
app.include_router(records.router, prefix=settings.api_prefix)
app.include_router(alerts.router, prefix=settings.api_prefix)
app.include_router(system.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    manager = get_market_data_manager()
    status = manager.get_market_status()
    ws_mgr = get_websocket_manager()
    feed_health = manager.get_feed_health()
    conn_status = feed_health.get("connection_status", "LIVE_DELAYED")

    broker_cfg = bool(
        os.getenv("ZERODHA_KITE_API_KEY")
        or os.getenv("UPSTOX_API_KEY")
        or os.getenv("ANGEL_ONE_API_KEY")
        or os.getenv("DHAN_CLIENT_ID")
        or os.getenv("BROKER_API_KEY")
    )

    return {
        "database": "OK",
        "redis": "OK" if os.getenv("REDIS_URL") else "SKIPPED",
        "market_data": conn_status,
        "websocket": "OK",
        "overall": "OK" if conn_status != "DISCONNECTED" else "DEGRADED",
        "status": "ok",
        "service": settings.app_name,
        "version": "2.0.0",
        "active_provider": manager.active_provider.provider_name if manager.active_provider else "NOT_INITIALIZED",
        "active_ws_clients": len(ws_mgr.active_connections),
        "broker": "configured" if broker_cfg else "unconfigured (using Yahoo Finance feed)",
        "market_session": status,
        "feed_health": feed_health,
    }


@app.websocket("/api/ws")
@app.websocket("/ws")
async def unified_websocket(websocket: WebSocket):
    import json
    from datetime import datetime, timezone

    trade_manager = TradeManager(get_store(settings.starting_capital))
    manager = get_market_data_manager()
    ws_mgr = get_websocket_manager()

    await ws_mgr.connect(websocket)
    logger.info("[MARKET] WebSocket client connected")

    tick_count = 0
    cached_signals = []
    cached_indices = {}
    cached_us_indices = {}
    cached_market_status = {}

    ws_lock = asyncio.Lock()
    cached_market_status = manager.get_market_status() if manager else {}

    async def _safe_send(payload_dict):
        try:
            async with ws_lock:
                await websocket.send_json(payload_dict)
        except Exception:
            pass

    # Handle incoming client messages (ping/pong, subscriptions) concurrently
    async def client_listener():
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    action = msg.get("action", "").lower()
                    if action == "ping":
                        await _safe_send({"type": "PONG", "timestamp": datetime.now(timezone.utc).isoformat()})
                    elif action == "subscribe":
                        symbols = msg.get("symbols", [])
                        await ws_mgr.subscribe(websocket, symbols)
                        logger.info(f"[MARKET] Subscription successful: {symbols[:5]}")
                        await _safe_send({
                            "type": "SUBSCRIBED",
                            "symbols": symbols,
                            "status": "OK",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    elif action == "unsubscribe":
                        symbols = msg.get("symbols", [])
                        await ws_mgr.unsubscribe(websocket, symbols)
                except (json.JSONDecodeError, ValueError):
                    pass
        except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
            return

    listener_task = asyncio.create_task(client_listener())

    try:
        while True:
            # ── HOT PATH (every 1 s): read from in-memory caches (Indian + US + Crypto 24/7) — zero blocking ──
            quotes_data = []
            if manager._primary_provider and manager._primary_provider._quote_cache:
                quotes_data.extend(list(manager._primary_provider._quote_cache.values()))
            if manager._international_provider and manager._international_provider._quote_cache:
                quotes_data.extend(list(manager._international_provider._quote_cache.values()))
            if manager._crypto_provider:
                quotes_data.extend(manager.get_crypto_quotes())

            # Instant fallback to in-memory cached quotes if provider cache is warming up (zero blocking)
            if not quotes_data and manager._cached_quotes:
                quotes_data = list(manager._cached_quotes.values())

            portfolio_data = await asyncio.to_thread(trade_manager.portfolio)

            # ── Real-time Data Quality & Staleness Telemetry ──
            quality_data = manager.get_data_quality()
            is_ai_paused = quality_data.get("ai_recommendations_paused", False)

            # ── WARM PATH (every 5 ticks = 5 s) ──
            if tick_count > 0 and tick_count % 5 == 0:
                try:
                    await asyncio.to_thread(trade_manager.evaluate_live_positions)
                except Exception:
                    pass
                try:
                    from app.services.market_data import get_indian_indices
                    cached_indices = await asyncio.to_thread(get_indian_indices)
                except Exception:
                    pass
                try:
                    cached_us_indices = await asyncio.to_thread(manager.get_us_indices)
                except Exception:
                    pass
                try:
                    cached_market_status = await asyncio.to_thread(manager.get_market_status)
                except Exception:
                    pass

            # ── COLD PATH (every 10 ticks = 10 s, skip tick 0) ──
            if tick_count > 0 and tick_count % 10 == 0:
                try:
                    cached_signals = await asyncio.to_thread(generate_ai_signals)
                except Exception:
                    pass

            # Automated pause of AI trade recommendations when feed is STALE or DISCONNECTED
            active_signals = [] if is_ai_paused else cached_signals[:5]

            def _clean_obj(item):
                if hasattr(item, "model_dump"):
                    return item.model_dump()
                if hasattr(item, "__dict__"):
                    return item.__dict__
                return item

            active_signals_clean = [_clean_obj(s) for s in active_signals]
            alerts_clean = [_clean_obj(a) for a in trade_manager.store.alerts[:5]]

            payload = {
                "type": "TICK_UPDATE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tick_count": tick_count,
                "update_rate": "1s",
                "quotes": quotes_data,
                "indices": cached_indices,
                "us_indices": cached_us_indices,
                "crypto": manager.get_crypto_quotes(),
                "portfolio": portfolio_data,
                "signals": active_signals_clean,
                "alerts": alerts_clean,
                "market_status": cached_market_status,
                "data_quality": quality_data,
                "feed_health": manager.get_feed_health(),
                "ai_safety": {
                    "recommendations_paused": is_ai_paused,
                    "pause_reason": quality_data.get("ai_pause_reason"),
                    "disclaimer": "AI predictions are probabilistic and do not guarantee future returns.",
                },
            }
            await _safe_send(payload)
            tick_count += 1
            await asyncio.sleep(1)
    except (WebSocketDisconnect, RuntimeError):
        return
    finally:
        listener_task.cancel()
        logger.info("[MARKET] WebSocket client disconnected")
        try:
            await ws_mgr.disconnect(websocket)
        except Exception:
            pass

