from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import alerts as alerts_router
from app.routers import ar as ar_router
from app.routers import auth as auth_router
from app.routers import claims as claims_router
from app.routers import staff as staff_router


limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting RCM Analytics API — env: {settings.app_env}")
    yield
    print("Shutting down RCM Analytics API")


app = FastAPI(
    title="RCM Analytics API",
    description=(
        "Healthcare Revenue Cycle Management Analytics Platform. "
        "Exposes KPIs for denial rates, AR days, and staff productivity."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(claims_router.router)
app.include_router(ar_router.router)
app.include_router(staff_router.router)
app.include_router(alerts_router.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "path": str(request.url.path),
        },
    )


@app.get("/", tags=["health"])
@limiter.limit("60/minute")
async def root(request: Request):
    return {
        "api": "RCM Analytics API",
        "version": "0.1.0",
        "status": "running",
        "env": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}