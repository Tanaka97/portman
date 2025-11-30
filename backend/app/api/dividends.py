from fastapi import APIRouter, Query, status
from app.models.schemas import Dividend, DividendCreate, SuccessResponse
from app.services.dividend_service import DividendService
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/dividends", tags=["dividends"])
dividend_service = DividendService()


@router.post("", response_model=Dividend, status_code=status.HTTP_201_CREATED)
def create_dividend(dividend_data: DividendCreate):
    """
    Record a dividend payment.
    """
    return dividend_service.create_dividend(dividend_data)


@router.get("", response_model=List[Dividend])
def get_dividends(
    portfolio_id: str = Query(...),
    symbol: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get dividend records for a portfolio.
    """
    return dividend_service.get_dividends(
        portfolio_id=portfolio_id,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/{dividend_id}", response_model=Dividend)
def get_dividend(dividend_id: str):
    """
    Get a specific dividend by ID.
    """
    return dividend_service.get_dividend(dividend_id)


@router.delete("/{dividend_id}", response_model=SuccessResponse)
def delete_dividend(dividend_id: str):
    """
    Delete a dividend record.
    """
    return dividend_service.delete_dividend(dividend_id)


@router.get("/total/{portfolio_id}")
def get_total_dividend_income(
    portfolio_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get total dividend income for a portfolio.
    """
    total = dividend_service.get_total_dividend_income(
        portfolio_id=portfolio_id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "portfolio_id": portfolio_id,
        "total_dividend_income": float(total),
        "start_date": start_date,
        "end_date": end_date
    }


@router.get("/by-symbol/{portfolio_id}")
def get_dividends_by_symbol(portfolio_id: str):
    """
    Get total dividends grouped by symbol.
    """
    return dividend_service.get_dividend_by_symbol(portfolio_id)
