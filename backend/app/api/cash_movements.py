"""
Cash movement API endpoints.
Track deposits and withdrawals.
"""

from fastapi import APIRouter, Query, status
from app.models.schemas import CashMovement, CashMovementCreate, SuccessResponse
from app.services.cash_movement_service import CashMovementService
from typing import List, Optional

router = APIRouter(prefix="/cash", tags=["cash-movements"])
cash_service = CashMovementService()


@router.post("", response_model=CashMovement, status_code=status.HTTP_201_CREATED)
def create_cash_movement(movement_data: CashMovementCreate):
    """
    Record a cash deposit or withdrawal.
    
    **Example request (deposit):**
```json
    {
      "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
      "amount": 5000.00,
      "type": "deposit",
      "movement_date": "2024-01-15T10:00:00",
      "notes": "Initial funding"
    }
```
    
    **Example request (withdrawal):**
```json
    {
      "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
      "amount": 1000.00,
      "type": "withdrawal",
      "movement_date": "2024-02-20T14:30:00",
      "notes": "Withdrew cash for expenses"
    }
```
    """
    return cash_service.create_cash_movement(movement_data)


@router.get("", response_model=List[CashMovement])
def get_cash_movements(
    portfolio_id: str = Query(..., description="Portfolio UUID"),
    movement_type: Optional[str] = Query(None, description="Filter by type (deposit/withdrawal)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get cash movements for a portfolio.
    
    **Query parameters:**
    - `portfolio_id`: (Required) Portfolio UUID
    - `movement_type`: (Optional) Filter by deposit or withdrawal
    - `limit`: Maximum number of movements to return
    
    Returns movements ordered by date (newest first).
    """
    return cash_service.get_cash_movements(
        portfolio_id=portfolio_id,
        movement_type=movement_type,
        limit=limit
    )


@router.get("/{movement_id}", response_model=CashMovement)
def get_cash_movement(movement_id: str):
    """
    Get a specific cash movement by ID.
    """
    return cash_service.get_cash_movement(movement_id)


@router.delete("/{movement_id}", response_model=SuccessResponse)
def delete_cash_movement(movement_id: str):
    """
    Delete a cash movement.
    """
    return cash_service.delete_cash_movement(movement_id)


@router.get("/balance/{portfolio_id}")
def get_cash_balance(portfolio_id: str):
    """
    Get current cash balance for a portfolio.
    
    Calculates: Total Deposits - Total Withdrawals
    """
    balance = cash_service.get_cash_balance(portfolio_id)
    return {
        "portfolio_id": portfolio_id,
        "cash_balance": float(balance)
    }