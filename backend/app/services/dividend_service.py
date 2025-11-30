from app.database import get_supabase_client
from app.models.schemas import DividendCreate, Dividend
from app.services.asset_service import AssetService
from typing import List, Optional
from fastapi import HTTPException
from decimal import Decimal
from datetime import date
import logging

logger = logging.getLogger(__name__)


class DividendService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.asset_service = AssetService()

    def create_dividend(self, dividend_data: DividendCreate) -> Dividend:
        try:
            portfolio_check = (
                self.supabase.table("portfolios")
                .select("id")
                .eq("id", dividend_data.portfolio_id)
                .execute()
            )

            if not portfolio_check.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio with id '{dividend_data.portfolio_id}' not found"
                )

            self.asset_service.get_or_create_asset(dividend_data.symbol)

            response = (
                self.supabase.table("dividends")
                .insert(dividend_data.model_dump())
                .execute()
            )

            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create dividend")

            logger.info(f"Created dividend: {dividend_data.symbol} - {dividend_data.amount}")
            return Dividend(**response.data[0])

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating dividend: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_dividends(
        self,
        portfolio_id: str,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dividend]:
        try:
            query = (
                self.supabase.table("dividends")
                .select("*")
                .eq("portfolio_id", portfolio_id)
            )

            if symbol:
                query = query.eq("symbol", symbol.upper())

            if start_date:
                query = query.gte("dividend_date", start_date.isoformat())

            if end_date:
                query = query.lte("dividend_date", end_date.isoformat())

            response = (
                query.order("dividend_date", desc=True)
                .limit(limit)
                .execute()
            )

            return [Dividend(**d) for d in response.data]

        except Exception as e:
            logger.error(f"Error fetching dividends: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_dividend(self, dividend_id: str) -> Dividend:
        try:
            response = (
                self.supabase.table("dividends")
                .select("*")
                .eq("id", dividend_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Dividend with id '{dividend_id}' not found"
                )

            return Dividend(**response.data[0])

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching dividend: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def delete_dividend(self, dividend_id: str) -> dict:
        try:
            self.get_dividend(dividend_id)

            self.supabase.table("dividends")\
                .delete()\
                .eq("id", dividend_id)\
                .execute()

            logger.info(f"Deleted dividend: {dividend_id}")

            return {"success": True, "message": "Dividend deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting dividend: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_total_dividend_income(
        self,
        portfolio_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        try:
            dividends = self.get_dividends(
                portfolio_id=portfolio_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )

            total = sum(d.amount for d in dividends)
            return Decimal(total)

        except Exception as e:
            logger.error(f"Error calculating dividend income: {e}")
            raise HTTPException(status_code=500, detail=str(e))
