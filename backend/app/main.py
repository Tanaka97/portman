"""
Main FastAPI application.
Updated for Phase 1 with complete schema support.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import get_supabase_client
from app.models.schemas import SuccessResponse
from typing import Dict
import logging

# Import all routers
from app.api.assets import router as assets_router
from app.api.portfolios import router as portfolios_router
from app.api.transactions import router as transactions_router
from app.api.positions import router as positions_router
from app.api.cash_movements import router as cash_router
from app.api.dividends import router as dividends_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Portfolio Manager API",
    description="Complete portfolio management system with multi-asset support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(assets_router)
app.include_router(portfolios_router)
app.include_router(transactions_router)
app.include_router(positions_router)
app.include_router(cash_router)
app.include_router(dividends_router)

# ================================================
# HEALTH CHECK ENDPOINTS
# ================================================

@app.get("/")
def read_root() -> Dict[str, str]:
    """
    Root endpoint - confirms API is running.
    """
    return {
        "message": "Portfolio Manager API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Multi-asset portfolio management",
            "Real-time position tracking",
            "Cash flow management",
            "Dividend tracking",
            "Asset allocation analysis",
            "CSV import from brokers"
        ]
    }

@app.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint - confirms API and database are healthy.
    """
    try:
        supabase = get_supabase_client()
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.environment,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# ================================================
# STARTUP/SHUTDOWN EVENTS
# ================================================

@app.on_event("startup")
async def startup_event():
    """
    Run when API starts up.
    """
    logger.info("🚀 Portfolio Manager API starting up...")
    logger.info(f"📝 Environment: {settings.environment}")
    logger.info(f"🗄️  Connecting to Supabase...")
    
    try:
        supabase = get_supabase_client()
        logger.info("✅ Database connection successful!")
        logger.info("✅ All services initialized!")
        logger.info("✅ API endpoints registered!")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Run when API shuts down.
    """
    logger.info("👋 Portfolio Manager API shutting down...")

# Run this file directly to start server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )