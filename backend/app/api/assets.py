"""
Asset API endpoints.
Manage stock/crypto metadata like sector, industry, etc.
"""

from fastapi import APIRouter, Query, status
from app.models.schemas import Asset, AssetCreate, AssetUpdate, SuccessResponse
from app.services.asset_service import AssetService
from typing import List

router = APIRouter(prefix="/assets", tags=["assets"])
asset_service = AssetService()


@router.post("", response_model=Asset, status_code=status.HTTP_201_CREATED)
def create_asset(asset_data: AssetCreate):
    """
    Create a new asset.
    
    **Note:** Assets are usually created automatically when you add transactions.
    Use this endpoint to add metadata (sector, industry, etc.) manually.
    
    **Example request:**
```json
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "country": "USA",
      "currency": "USD",
      "exchange": "NASDAQ"
    }
```
    """
    return asset_service.get_or_create_asset(asset_data.ticker, asset_data)


@router.get("", response_model=List[Asset])
def get_all_assets(limit: int = Query(1000, ge=1, le=10000)):
    """
    Get all assets.
    
    Returns list of all assets in the database with their metadata.
    """
    return asset_service.get_all_assets(limit=limit)


@router.get("/search", response_model=List[Asset])
def search_assets(q: str = Query(..., min_length=1, description="Search query")):
    """
    Search assets by ticker or name.
    
    **Example:** `/assets/search?q=apple` finds AAPL and any other assets with "apple" in the name.
    """
    return asset_service.search_assets(q)


@router.get("/{ticker}", response_model=Asset)
def get_asset(ticker: str):
    """
    Get a specific asset by ticker symbol.
    
    **Example:** `/assets/AAPL` returns Apple Inc. metadata.
    """
    return asset_service.get_asset(ticker)


@router.put("/{ticker}", response_model=Asset)
def update_asset(ticker: str, asset_data: AssetUpdate):
    """
    Update asset metadata.
    
    **Example request:**
```json
    {
      "sector": "Technology",
      "industry": "Consumer Electronics"
    }
```
    
    All fields are optional - only include fields you want to update.
    """
    return asset_service.update_asset(ticker, asset_data)