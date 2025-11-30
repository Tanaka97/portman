"""
Pydantic schemas for request/response validation.
Updated to match new database schema with assets table and additional features.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ================================================
# PORTFOLIO SCHEMAS
# ================================================

class PortfolioBase(BaseModel):
    """Base portfolio schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    description: Optional[str] = Field(None, max_length=500, description="Portfolio description")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code (USD, EUR, GBP)")


class PortfolioCreate(PortfolioBase):
    """
    Schema for creating a new portfolio.
    Note: user_id will be added automatically in Phase 2 when we add authentication.
    For now, we use a test user_id.
    """
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)


class Portfolio(PortfolioBase):
    """Complete portfolio schema with database fields"""
    id: str
    user_id: str  # NEW: Required by schema
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# ASSET SCHEMAS (NEW!)
# ================================================

class AssetBase(BaseModel):
    """Base asset schema"""
    ticker: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    name: Optional[str] = Field(None, description="Company/asset name")
    sector: Optional[str] = Field(None, max_length=100, description="Sector (Technology, Healthcare, etc.)")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Trading currency")
    exchange: Optional[str] = Field(None, max_length=50, description="Exchange (NASDAQ, NYSE, etc.)")


class AssetCreate(AssetBase):
    """Schema for creating a new asset"""
    pass


class AssetUpdate(BaseModel):
    """Schema for updating an asset (all fields optional)"""
    name: Optional[str] = None
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    exchange: Optional[str] = Field(None, max_length=50)


class Asset(AssetBase):
    """Complete asset schema with database fields"""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# TRANSACTION SCHEMAS
# ================================================

class TransactionBase(BaseModel):
    """
    Base transaction schema.
    Note: In the new schema, transactions reference the assets table.
    """
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock/crypto symbol (AAPL, BTC, etc.)")
    transaction_type: str = Field(..., description="Transaction type: buy, sell, dividend, split, transfer_in, transfer_out")
    quantity: Optional[Decimal] = Field(None, ge=0, description="Quantity (optional for dividends)")
    price: Optional[Decimal] = Field(None, ge=0, description="Price per unit (optional for dividends)")
    fees: Optional[Decimal] = Field(default=Decimal("0"), ge=0, description="Transaction fees")
    transaction_date: datetime = Field(..., description="Date/time of transaction")
    notes: Optional[str] = Field(None, description="Optional notes")
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        """Ensure transaction type is valid"""
        valid_types = ['buy', 'sell', 'dividend', 'split', 'transfer_in', 'transfer_out']
        if v.lower() not in valid_types:
            raise ValueError(f'transaction_type must be one of: {", ".join(valid_types)}')
        return v.lower()
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Convert symbol to uppercase"""
        return v.upper().strip()


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction"""
    portfolio_id: str = Field(..., description="Portfolio UUID")


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction (all fields optional)"""
    symbol: Optional[str] = Field(None, min_length=1, max_length=20)
    transaction_type: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, ge=0)
    price: Optional[Decimal] = Field(None, ge=0)
    fees: Optional[Decimal] = Field(None, ge=0)
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v:
            valid_types = ['buy', 'sell', 'dividend', 'split', 'transfer_in', 'transfer_out']
            if v.lower() not in valid_types:
                raise ValueError(f'transaction_type must be one of: {", ".join(valid_types)}')
            return v.lower()
        return v


class Transaction(TransactionBase):
    """Complete transaction schema with database fields"""
    id: str
    portfolio_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# POSITION SCHEMAS
# ================================================

class Position(BaseModel):
    """
    Current position (holding) schema.
    Enhanced with asset information from assets table.
    """
    id: str
    portfolio_id: str
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    total_cost: Decimal
    unrealized_gain_loss: Optional[Decimal] = None
    unrealized_gain_loss_percent: Optional[Decimal] = None
    last_price_update: Optional[datetime] = None
    
    # Asset information (joined from assets table)
    asset_name: Optional[str] = None
    asset_sector: Optional[str] = None
    asset_industry: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# CASH MOVEMENT SCHEMAS (NEW!)
# ================================================

class CashMovementBase(BaseModel):
    """Base cash movement schema"""
    amount: Decimal = Field(..., description="Amount (positive for deposits, will be stored as-is)")
    type: str = Field(..., description="Movement type: deposit or withdrawal")
    movement_date: datetime = Field(..., description="Date of cash movement")
    notes: Optional[str] = Field(None, description="Optional notes")
    
    @validator('type')
    def validate_type(cls, v):
        """Ensure type is valid"""
        if v.lower() not in ['deposit', 'withdrawal']:
            raise ValueError('type must be "deposit" or "withdrawal"')
        return v.lower()


class CashMovementCreate(CashMovementBase):
    """Schema for creating a cash movement"""
    portfolio_id: str = Field(..., description="Portfolio UUID")


class CashMovement(CashMovementBase):
    """Complete cash movement schema with database fields"""
    id: str
    portfolio_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# DIVIDEND SCHEMAS (NEW!)
# ================================================

class DividendBase(BaseModel):
    """Base dividend schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    amount: Decimal = Field(..., description="Dividend amount")
    dividend_date: datetime = Field(..., description="Ex-dividend date")
    dividend_type: Optional[str] = Field(None, max_length=50, description="Type (cash, stock, special)")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Convert symbol to uppercase"""
        return v.upper().strip()


class DividendCreate(DividendBase):
    """Schema for creating a dividend record"""
    portfolio_id: str = Field(..., description="Portfolio UUID")


class Dividend(DividendBase):
    """Complete dividend schema with database fields"""
    id: str
    portfolio_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# PERFORMANCE SNAPSHOT SCHEMAS (NEW!)
# ================================================

class PerformanceSnapshotBase(BaseModel):
    """Base performance snapshot schema"""
    snapshot_date: date = Field(..., description="Date of snapshot")
    total_value: Optional[Decimal] = Field(None, description="Total portfolio value")
    total_cost: Optional[Decimal] = Field(None, description="Total cost basis")
    pnl: Optional[Decimal] = Field(None, description="Profit and loss")


class PerformanceSnapshotCreate(PerformanceSnapshotBase):
    """Schema for creating a performance snapshot"""
    portfolio_id: str = Field(..., description="Portfolio UUID")


class PerformanceSnapshot(PerformanceSnapshotBase):
    """Complete performance snapshot schema"""
    id: str
    portfolio_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ================================================
# CSV IMPORT SCHEMAS
# ================================================

class CSVImportRequest(BaseModel):
    """Schema for CSV import request"""
    portfolio_id: str = Field(..., description="Portfolio to import into")
    broker_format: str = Field(..., description="Broker format (generic, robinhood, interactivebrokers, etc.)")
    csv_data: str = Field(..., description="CSV file content as string")


class CSVImportResponse(BaseModel):
    """Schema for CSV import response"""
    success: bool
    imported_count: int
    failed_count: int
    errors: List[str] = []
    transactions: List[Transaction] = []


# ================================================
# PORTFOLIO SUMMARY SCHEMAS
# ================================================

class PortfolioSummary(BaseModel):
    """Summary statistics for a portfolio"""
    portfolio_id: str
    portfolio_name: str
    total_value: Decimal
    total_cost: Decimal
    total_gain_loss: Decimal
    total_gain_loss_percent: Decimal
    cash_balance: Decimal  # NEW: From cash_movements
    position_count: int
    transaction_count: int
    dividend_income: Decimal  # NEW: Total dividends
    last_updated: datetime


class AllocationItem(BaseModel):
    """Single allocation item"""
    category: str  # sector, industry, or asset type
    total_value: Decimal
    percentage: Decimal
    position_count: int


class PortfolioAllocation(BaseModel):
    """Asset allocation breakdown"""
    by_sector: List[AllocationItem]
    by_industry: List[AllocationItem]
    by_country: List[AllocationItem]


# ================================================
# RESPONSE WRAPPERS
# ================================================

class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None