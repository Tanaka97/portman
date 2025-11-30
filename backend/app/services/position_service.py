"""
Position service - handles position calculations and queries.
Updated to join with assets table for sector/industry information.
"""

from app.database import get_supabase_client
from app.models.schemas import Position
from app.services.cash_movement_service import CashMovementService
from app.services.dividend_service import DividendService
from typing import List, Optional
from fastapi import HTTPException
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PositionService:
    """Service class for position operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.cash_service = CashMovementService()
        self.dividend_service = DividendService()
    
    def get_positions(
        self,
        portfolio_id: str,
        symbol: Optional[str] = None
    ) -> List[Position]:
        """
        Get positions for a portfolio with asset information.
        
        Args:
            portfolio_id: Portfolio UUID
            symbol: Optional symbol filter
            
        Returns:
            List of positions with calculated values and asset metadata
        """
        try:
            query = self.supabase.table("positions")\
                .select("*, assets(name, sector, industry)")\
                .eq("portfolio_id", portfolio_id)
            
            if symbol:
                query = query.eq("symbol", symbol.upper())
            
            response = query.execute()
            
            # Enhance positions with calculated fields and asset data
            positions = []
            for pos_data in response.data:
                position = self._enhance_position(pos_data)
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_position(self, position_id: str) -> Position:
        """
        Get a specific position by ID.
        
        Args:
            position_id: Position UUID
            
        Returns:
            Position object with calculated values
            
        Raises:
            HTTPException: If position not found
        """
        try:
            response = self.supabase.table("positions")\
                .select("*, assets(name, sector, industry)")\
                .eq("id", position_id)\
                .execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Position with id '{position_id}' not found"
                )
            
            return self._enhance_position(response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching position: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _enhance_position(self, pos_data: dict) -> Position:
        """
        Add calculated fields and asset information to position data.
        
        Args:
            pos_data: Raw position data from database (with joined assets)
            
        Returns:
            Position object with calculated values
        """
        quantity = Decimal(str(pos_data["quantity"]))
        average_cost = Decimal(str(pos_data["average_cost"]))
        current_price = Decimal(str(pos_data.get("current_price", 0))) if pos_data.get("current_price") else None
        
        # Calculate total cost
        total_cost = quantity * average_cost
        
        # Calculate current value and gains if we have a current price
        current_value = None
        unrealized_gain_loss = None
        unrealized_gain_loss_percent = None
        
        if current_price:
            current_value = quantity * current_price
            unrealized_gain_loss = current_value - total_cost
            
            if total_cost > 0:
                unrealized_gain_loss_percent = (unrealized_gain_loss / total_cost) * 100
        
        # Extract asset information from join
        asset_data = pos_data.get("assets", {})
        if isinstance(asset_data, dict):
            asset_name = asset_data.get("name")
            asset_sector = asset_data.get("sector")
            asset_industry = asset_data.get("industry")
        else:
            asset_name = None
            asset_sector = None
            asset_industry = None
        
        # Add calculated fields to position data
        enhanced_data = {
            "id": pos_data["id"],
            "portfolio_id": pos_data["portfolio_id"],
            "symbol": pos_data["symbol"],
            "quantity": quantity,
            "average_cost": average_cost,
            "current_price": current_price,
            "current_value": current_value,
            "total_cost": total_cost,
            "unrealized_gain_loss": unrealized_gain_loss,
            "unrealized_gain_loss_percent": unrealized_gain_loss_percent,
            "last_price_update": pos_data.get("last_price_update"),
            "asset_name": asset_name,
            "asset_sector": asset_sector,
            "asset_industry": asset_industry,
            "created_at": pos_data["created_at"],
            "updated_at": pos_data["updated_at"]
        }
        
        return Position(**enhanced_data)
    
    def get_portfolio_summary(self, portfolio_id: str) -> dict:
        """
        Get comprehensive summary statistics for a portfolio.
        
        Args:
            portfolio_id: Portfolio UUID
            
        Returns:
            Summary statistics including positions, cash, dividends
        """
        try:
            # Get portfolio name
            portfolio_response = self.supabase.table("portfolios")\
                .select("name")\
                .eq("id", portfolio_id)\
                .execute()
            
            if not portfolio_response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio with id '{portfolio_id}' not found"
                )
            
            portfolio_name = portfolio_response.data[0]["name"]
            
            # Get all positions
            positions = self.get_positions(portfolio_id)
            
            # Calculate position totals
            total_value = Decimal("0")
            total_cost = Decimal("0")
            position_count = len(positions)
            
            for position in positions:
                total_cost += position.total_cost
                if position.current_value:
                    total_value += position.current_value
                else:
                    # If no current price, use cost as value
                    total_value += position.total_cost
            
            # Calculate gains
            total_gain_loss = total_value - total_cost
            total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else Decimal("0")
            
            # Get cash balance
            cash_balance = self.cash_service.get_cash_balance(portfolio_id)
            
            # Get total dividend income
            dividend_income = self.dividend_service.get_total_dividend_income(portfolio_id)
            
            # Get transaction count
            tx_response = self.supabase.table("transactions")\
                .select("id", count="exact")\
                .eq("portfolio_id", portfolio_id)\
                .execute()
            
            transaction_count = tx_response.count if hasattr(tx_response, 'count') else len(tx_response.data)
            
            # Add cash to total value
            total_value += cash_balance
            
            from datetime import datetime
            
            return {
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio_name,
                "total_value": float(total_value),
                "total_cost": float(total_cost),
                "total_gain_loss": float(total_gain_loss),
                "total_gain_loss_percent": float(total_gain_loss_percent),
                "cash_balance": float(cash_balance),
                "position_count": position_count,
                "transaction_count": transaction_count,
                "dividend_income": float(dividend_income),
                "last_updated": datetime.now()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating portfolio summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_allocation_by_sector(self, portfolio_id: str) -> List[dict]:
        """
        Get portfolio allocation breakdown by sector.
        
        Args:
            portfolio_id: Portfolio UUID
            
        Returns:
            List of allocations by sector
        """
        try:
            positions = self.get_positions(portfolio_id)
            
            # Group by sector
            allocations = {}
            total_value = Decimal("0")
            
            for position in positions:
                sector = position.asset_sector or "Unknown"
                value = position.current_value or position.total_cost
                
                if sector not in allocations:
                    allocations[sector] = {
                        "value": Decimal("0"),
                        "count": 0
                    }
                
                allocations[sector]["value"] += value
                allocations[sector]["count"] += 1
                total_value += value
            
            # Calculate percentages
            result = []
            for sector, data in allocations.items():
                percentage = (data["value"] / total_value * 100) if total_value > 0 else Decimal("0")
                result.append({
                    "category": sector,
                    "total_value": float(data["value"]),
                    "percentage": float(percentage),
                    "position_count": data["count"]
                })
            
            # Sort by value descending
            result.sort(key=lambda x: x["total_value"], reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating sector allocation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_allocation_by_industry(self, portfolio_id: str) -> List[dict]:
        """
        Get portfolio allocation breakdown by industry.
        
        Args:
            portfolio_id: Portfolio UUID
            
        Returns:
            List of allocations by industry
        """
        try:
            positions = self.get_positions(portfolio_id)
            
            # Group by industry
            allocations = {}
            total_value = Decimal("0")
            
            for position in positions:
                industry = position.asset_industry or "Unknown"
                value = position.current_value or position.total_cost
                
                if industry not in allocations:
                    allocations[industry] = {
                        "value": Decimal("0"),
                        "count": 0
                    }
                
                allocations[industry]["value"] += value
                allocations[industry]["count"] += 1
                total_value += value
            
            # Calculate percentages
            result = []
            for industry, data in allocations.items():
                percentage = (data["value"] / total_value * 100) if total_value > 0 else Decimal("0")
                result.append({
                    "category": industry,
                    "total_value": float(data["value"]),
                    "percentage": float(percentage),
                    "position_count": data["count"]
                })
            
            # Sort by value descending
            result.sort(key=lambda x: x["total_value"], reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating industry allocation: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_comprehensive_allocation(self, portfolio_id: str) -> dict:
        """
        Get comprehensive allocation breakdown by sector, industry, and country.
        
        Args:
            portfolio_id: Portfolio UUID
            
        Returns:
            Dictionary with allocations by different categories
        """
        try:
            return {
                "by_sector": self.get_allocation_by_sector(portfolio_id),
                "by_industry": self.get_allocation_by_industry(portfolio_id)
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive allocation: {e}")
            raise HTTPException(status_code=500, detail=str(e))