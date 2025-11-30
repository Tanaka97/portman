"""
Position API endpoints.
Updated to include asset information.
"""

from fastapi import APIRouter, Query
from app.models.schemas import Position
from app.services.position_service import PositionService
from typing import List, Optional

router = APIRouter(prefix="/positions", tags=["positions"])
position_service = PositionService()


@router.get("", response_model=List[Position])
def get_positions(
    portfolio_id: str = Query(..., description="Portfolio UUID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Get positions for a portfolio.
    
    **Query parameters:**
    - `portfolio_id`: (Required) Portfolio UUID
    - `symbol`: (Optional) Filter by specific symbol
    
    Returns current positions with:
    - Total cost basis
    - Current value (if price available)
    - Unrealized gain/loss
    - Percentage gain/loss
    - Asset metadata (name, sector, industry)
    """
    return position_service.get_positions(
        portfolio_id=portfolio_id,
        symbol=symbol
    )


@router.get("/{position_id}", response_model=Position)
def get_position(position_id: str):
    """
    Get a specific position by ID.
    
    **Parameters:**
    - `position_id`: UUID of the position
    
    Returns position with asset information and calculated values.
    """
    return position_service.get_position(position_id)