"""
Transaction API endpoints.
Updated to support new transaction types.
"""

from fastapi import APIRouter, Query, status
from app.models.schemas import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    SuccessResponse
)
from app.services.transaction_service import TransactionService
from typing import List, Optional

router = APIRouter(prefix="/transactions", tags=["transactions"])
transaction_service = TransactionService()


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction_data: TransactionCreate):
    """
    Create a new transaction.
    
    **Supported transaction types:**
    - `buy`: Purchase assets
    - `sell`: Sell assets
    - `dividend`: Dividend payment (use /dividends endpoint instead)
    - `split`: Stock split
    - `transfer_in`: Transfer assets into portfolio
    - `transfer_out`: Transfer assets out of portfolio
    
    **Example request (buy):**
```json
    {
      "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
      "symbol": "AAPL",
      "transaction_type": "buy",
      "quantity": 10,
      "price": 150.50,
      "fees": 0,
      "transaction_date": "2024-01-15T10:30:00",
      "notes": "Purchased through broker"
    }
```
    
    **Note:** 
    - Asset is created automatically if it doesn't exist
    - Positions are automatically recalculated after transaction
    """
    return transaction_service.create_transaction(transaction_data)


@router.get("", response_model=List[Transaction])
def get_transactions(
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    transaction_type: Optional[str] = Query(None, description="Filter by type (buy, sell, etc.)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """
    Get transactions with optional filters.
    
    **Query parameters:**
    - `portfolio_id`: Only show transactions from this portfolio
    - `symbol`: Only show transactions for this symbol
    - `transaction_type`: Filter by type (buy, sell, dividend, etc.)
    - `limit`: Maximum number of transactions to return (default: 100)
    
    Returns transactions ordered by date (newest first).
    """
    return transaction_service.get_transactions(
        portfolio_id=portfolio_id,
        symbol=symbol,
        transaction_type=transaction_type,
        limit=limit
    )


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: str):
    """
    Get a specific transaction by ID.
    
    **Parameters:**
    - `transaction_id`: UUID of the transaction
    """
    return transaction_service.get_transaction(transaction_id)


@router.put("/{transaction_id}", response_model=Transaction)
def update_transaction(transaction_id: str, transaction_data: TransactionUpdate):
    """
    Update a transaction.
    
    **Parameters:**
    - `transaction_id`: UUID of the transaction
    
    **Example request:**
```json
    {
      "quantity": 15,
      "notes": "Updated quantity"
    }
```
    
    All fields are optional - only include fields you want to update.
    
    **Note:** After updating, positions are automatically recalculated.
    """
    return transaction_service.update_transaction(transaction_id, transaction_data)


@router.delete("/{transaction_id}", response_model=SuccessResponse)
def delete_transaction(transaction_id: str):
    """
    Delete a transaction.
    
    **Note:** After deleting, positions are automatically recalculated.
    """
    return transaction_service.delete_transaction(transaction_id)