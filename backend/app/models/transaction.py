from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"

class TransactionCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    transaction_type: TransactionType
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fees: float = Field(0, ge=0)
    transaction_date: datetime
    notes: Optional[str] = None
    asset_class: Optional[str] = None
    sector: Optional[str] = None

class TransactionResponse(BaseModel):
    id: UUID
    portfolio_id: UUID
    symbol: str
    transaction_type: TransactionType
    quantity: float
    price: float
    fees: float
    transaction_date: datetime
    notes: Optional[str]
    asset_class: Optional[str]
    sector: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True