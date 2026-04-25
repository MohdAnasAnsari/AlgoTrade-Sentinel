import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_database, shutdown_database
from app.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.scheduler import shutdown_scheduler, start_scheduler
from app.routers import alerts
from app.routers import dashboard
from app.routers import health
from app.routers import market
from app.routers import features
from app.routers import training
from app.routers import backtest
from app.routers import signals
from app.routers import registry
from app.routers import monitoring
from app.routers import portfolio
from app.routers import settings as settings_router
from app.routers import system
from app.routers import watchlist

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address

    HAS_SLOWAPI = True
except Exception:  # pragma: no cover - optional dependency fallback
    Limiter = None  # type: ignore[assignment]
    RateLimitExceeded = None  # type: ignore[assignment]
    SlowAPIMiddleware = None  # type: ignore[assignment]
    HAS_SLOWAPI = False


limiter = (
    Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
    if HAS_SLOWAPI
    else None
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()
        shutdown_database()


app = FastAPI(
    title="AlgoTrade Sentinel API",
    description="AI-powered trading research, signal intelligence, and MLOps platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

if limiter is not None and RateLimitExceeded is not None and SlowAPIMiddleware is not None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
else:
    logger.warning("slowapi is not installed; request rate limiting is disabled")

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if settings.ENABLE_REQUEST_LOGGING:
    app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(market.router)
app.include_router(features.router)
app.include_router(training.router)
app.include_router(backtest.router)
app.include_router(signals.router)
app.include_router(registry.router)
app.include_router(monitoring.router)
app.include_router(system.router)
app.include_router(portfolio.router)
app.include_router(alerts.router)
app.include_router(watchlist.router)
app.include_router(settings_router.router)
app.include_router(dashboard.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "details": exc.detail if not isinstance(exc.detail, str) else None,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "details": {"type": type(exc).__name__},
            }
        },
    )
