"""
Portfolio API endpoints.
Updated to work with new schema and allocation features.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    SuccessResponse
)
from app.services.portfolio_service import PortfolioService
from app.services.position_service import PositionService
from typing import List

router = APIRouter(prefix="/portfolios", tags=["portfolios"])
portfolio_service = PortfolioService()
position_service = PositionService()


@router.post("", response_model=Portfolio, status_code=status.HTTP_201_CREATED)
def create_portfolio(portfolio_data: PortfolioCreate):
    """
    Create a new portfolio.
    
    **Example request:**
```json
    {
      "name": "Tech Stocks Portfolio",
      "description": "My technology stock investments",
      "currency": "USD"
    }
```
    
    **Note:** user_id is automatically set for now (TEST_USER_ID).
    In Phase 2, this will use real authentication.
    """
    return portfolio_service.create_portfolio(portfolio_data)


@router.get("", response_model=List[Portfolio])
def get_all_portfolios():
    """
    Get all portfolios for the current user.
    
    Returns a list of all portfolios ordered by creation date (newest first).
    """
    return portfolio_service.get_all_portfolios()


@router.get("/{portfolio_id}", response_model=Portfolio)
def get_portfolio(portfolio_id: str):
    """
    Get a specific portfolio by ID.
    
    **Parameters:**
    - `portfolio_id`: UUID of the portfolio
    """
    return portfolio_service.get_portfolio(portfolio_id)


@router.put("/{portfolio_id}", response_model=Portfolio)
def update_portfolio(portfolio_id: str, portfolio_data: PortfolioUpdate):
    """
    Update a portfolio.
    
    **Parameters:**
    - `portfolio_id`: UUID of the portfolio
    
    **Example request:**
```json
    {
      "name": "Updated Portfolio Name",
      "description": "New description"
    }
```
    
    All fields are optional - only include fields you want to update.
    """
    return portfolio_service.update_portfolio(portfolio_id, portfolio_data)


@router.delete("/{portfolio_id}", response_model=SuccessResponse)
def delete_portfolio(portfolio_id: str):
    """
    Delete a portfolio and all associated data.
    
    **Warning:** This will permanently delete:
    - The portfolio
    - All transactions
    - All positions
    - All cash movements
    - All dividend records
    
    This action cannot be undone!
    """
    return portfolio_service.delete_portfolio(portfolio_id)


@router.get("/{portfolio_id}/summary")
def get_portfolio_summary(portfolio_id: str):
    """
    Get comprehensive summary statistics for a portfolio.
    
    Returns:
    - Total value (positions + cash)
    - Total cost basis
    - Total gain/loss
    - Cash balance
    - Position count
    - Transaction count
    - Total dividend income
    """
    return position_service.get_portfolio_summary(portfolio_id)


@router.get("/{portfolio_id}/allocation")
def get_portfolio_allocation(portfolio_id: str):
    """
    Get comprehensive asset allocation breakdown.
    
    Returns allocation by:
    - Sector (Technology, Healthcare, etc.)
    - Industry (Consumer Electronics, Pharmaceuticals, etc.)
    
    Each category shows:
    - Total value
    - Percentage of portfolio
    - Number of positions
    """
    return position_service.get_comprehensive_allocation(portfolio_id)


@router.get("/{portfolio_id}/allocation/sector")
def get_sector_allocation(portfolio_id: str):
    """
    Get allocation breakdown by sector only.
    """
    return position_service.get_allocation_by_sector(portfolio_id)


@router.get("/{portfolio_id}/allocation/industry")
def get_industry_allocation(portfolio_id: str):
    """
    Get allocation breakdown by industry only.
    """
    return position_service.get_allocation_by_industry(portfolio_id)