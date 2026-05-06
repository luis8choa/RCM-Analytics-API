from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth as auth_router
from app.routers import claims as claims_router
from app.routers import ar as ar_router


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

@app.get("/", tags=["health"])
def root():
    return {
        "api": "RCM Analytics API",
        "version": "0.1.0",
        "status": "running",
        "env": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}