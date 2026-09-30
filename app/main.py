from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import (
    auth_router,
    centres_router,
    tests_router,
    centre_tests_router,
    bookings_router,
    payments_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready Diagnostic Test Bookings and Payment Processing API for EVE Healthcare.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API V1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(centres_router, prefix=settings.API_V1_STR)
app.include_router(tests_router, prefix=settings.API_V1_STR)
app.include_router(centre_tests_router, prefix=settings.API_V1_STR)
app.include_router(bookings_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}
