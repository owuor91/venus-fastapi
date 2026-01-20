from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, matches, photos, payments, payment_plans
from app.core.config import settings

app = FastAPI(
    title="Venus Dating App API",
    description="REST API for a dating app built with FastAPI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(photos.router, prefix="/api/v1/photos", tags=["photos"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(payment_plans.router, prefix="/api/v1/payment-plans", tags=["payment-plans"])


@app.get("/")
def root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to Venus Dating App API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
