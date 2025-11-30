"""
Cash movement service - handles deposits and withdrawals.
"""

from app.database import get_supabase_client
from app.models.schemas import CashMovementCreate, CashMovement
from typing import List, Optional
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CashMovementService:
    """Service class for cash movement operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def create_cash_movement(self, movement_data: CashMovementCreate) -> CashMovement:
        """
        Record a cash deposit or withdrawal.
        
        Args:
            movement_data: Cash movement data
            
        Returns:
            Created cash movement
            
        Raises:
            HTTPException: If portfolio not found or creation fails
        """
        try:
            # Verify portfolio exists
            portfolio_check = self.supabase.table("portfolios")\
                .select("id")\
                .eq("id", movement_data.portfolio_id)\
                .execute()
            
            if not portfolio_check.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio with id '{movement_data.portfolio_id}' not found"
                )
            
            # Insert cash movement
            response = self.supabase.table("cash_movements")\
                .insert(movement_data.model_dump())\
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create cash movement")
            
            logger.info(f"Created cash movement: {movement_data.type} - ${movement_data.amount}")
            return CashMovement(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating cash movement: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_cash_movements(
        self,
        portfolio_id: str,
        movement_type: Optional[str] = None,
        limit: int = 100
    ) -> List[CashMovement]:
        """
        Get cash movements for a portfolio.
        
        Args:
            portfolio_id: Portfolio UUID
            movement_type: Filter by type (deposit/withdrawal)
            limit: Maximum number of movements to return
            
        Returns:
            List of cash movements
        """
        try:
            query = self.supabase.table("cash_movements")\
                .select("*")\
                .eq("portfolio_id", portfolio_id)
            
            if movement_type:
                query = query.eq("type", movement_type.lower())
            
            response = query.order("movement_date", desc=True)\
                .limit(limit)\
                .execute()
            
            return [CashMovement(**m) for m in response.data]
            
        except Exception as e:
            logger.error(f"Error fetching cash movements: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_cash_movement(self, movement_id: str) -> CashMovement:
        """
        Get a specific cash movement by ID.
        
        Args:
            movement_id: Cash movement UUID
            
        Returns:
            Cash movement object
            
        Raises:
            HTTPException: If movement not found
        """
        try:
            response = self.supabase.table("cash_movements")\
                .select("*")\
                .eq("id", movement_id)\
                .execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Cash movement with id '{movement_id}' not found"
                )
            
            return CashMovement(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching cash movement: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_cash_movement(self, movement_id: str) -> dict:
        """
        Delete a cash movement.
        
        Args:
            movement_id: Cash movement UUID
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If movement not found or deletion fails
        """
        try:
            # Get movement to verify it exists
            movement = self.get_cash_movement(movement_id)
            
            # Delete movement
            self.supabase.table("cash_movements")\
                .delete()\
                .eq("id", movement_id)\
                .execute()
            
            logger.info(f"Deleted cash movement: {movement_id}")
            return {
                "success": True,
                "message": "Cash movement deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting cash movement: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_cash_balance(self, portfolio_id: str) -> Decimal:
        """
        Calculate current cash balance for a portfolio.
        
        Args:
            portfolio_id: Portfolio UUID
            
        Returns:
            Current cash balance (deposits - withdrawals)
        """
        try:
            # Get all cash movements
            movements = self.get_cash_movements(portfolio_id, limit=10000)
            
            balance = Decimal("0")
            for movement in movements:
                if movement.type == "deposit":
                    balance += movement.amount
                else:  # withdrawal
                    balance -= movement.amount
            
            return balance
            
        except Exception as e:
            logger.error(f"Error calculating cash balance: {e}")
            raise HTTPException(status_code=500, detail=str(e))