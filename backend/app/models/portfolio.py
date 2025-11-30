from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    currency: str = Field("USD", pattern="^(USD|EUR|GBP|JPY)$")

class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    currency: Optional[str] = Field(None, pattern="^(USD|EUR|GBP|JPY)$")

class PortfolioResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True