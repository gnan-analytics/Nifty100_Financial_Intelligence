import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description=(
        "REST API for Nifty 100 company fundamentals, "
        "screening, peers, valuation and portfolio analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(
    request: Request,
    call_next,
):
    """Log request method, path, status code, and response time."""

    start = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000

    print(
        f"{request.method} "
        f"{request.url.path} "
        f"{response.status_code} "
        f"{elapsed_ms:.2f}ms"
    )

    return response


app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"],
)

app.include_router(
    companies.router,
    prefix="/api/v1",
    tags=["Companies"],
)

app.include_router(
    screener.router,
    prefix="/api/v1",
    tags=["Screener"],
)

app.include_router(
    sectors.router,
    prefix="/api/v1",
    tags=["Sectors"],
)

app.include_router(
    peers.router,
    prefix="/api/v1",
    tags=["Peers"],
)

app.include_router(
    valuation.router,
    prefix="/api/v1",
    tags=["Valuation"],
)

app.include_router(
    portfolio.router,
    prefix="/api/v1",
    tags=["Portfolio"],
)

app.include_router(
    documents.router,
    prefix="/api/v1",
    tags=["Documents"],
)


@app.get("/")
def root():
    """Return basic API information."""

    return {
        "name": "Nifty 100 Financial Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
