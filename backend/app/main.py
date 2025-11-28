"""
Main FastAPI application.
This is the entry point for our Portfolio Manager API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import get_supabase_client
from typing import Dict, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Portfolio Manager API",
    description="API for managing investment portfolios",
    version="0.1.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

# Add CORS middleware (allows frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint - confirms API and database are healthy.
    """
    try:
        # Try to get Supabase client
        supabase = get_supabase_client()
        
        return {
            "status": "healthy",
            "database": "connected",
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# ================================================
# PORTFOLIO ENDPOINTS
# ================================================

@app.get("/portfolios")
def get_portfolios() -> Dict[str, List]:
    """
    Get all portfolios.
    
    Returns:
        List of all portfolios in the database
    """
    try:
        supabase = get_supabase_client()
        
        # Query portfolios table
        response = supabase.table("portfolios").select("*").execute()
        
        return {
            "success": True,
            "count": len(response.data),
            "portfolios": response.data
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: str) -> Dict:
    """
    Get a specific portfolio by ID.
    
    Args:
        portfolio_id: UUID of the portfolio
        
    Returns:
        Portfolio details
    """
    try:
        supabase = get_supabase_client()
        
        # Query specific portfolio
        response = supabase.table("portfolios")\
            .select("*")\
            .eq("id", portfolio_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return {
            "success": True,
            "portfolio": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        # Test database connection
        supabase = get_supabase_client()
        logger.info("✅ Database connection successful!")
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
        reload=True  # Auto-reload on code changes
    )