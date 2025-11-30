"""
Transaction service - handles all transaction-related business logic.
Updated to work with assets table and new schema.
"""

from app.database import get_supabase_client
from app.models.schemas import TransactionCreate, TransactionUpdate, Transaction
from app.services.asset_service import AssetService
from typing import List, Optional
from fastapi import HTTPException
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class TransactionService:
    """Service class for transaction operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.asset_service = AssetService()
    
    def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            transaction_data: Transaction creation data
            
        Returns:
            Created transaction
            
        Raises:
            HTTPException: If portfolio not found or creation fails
        """
        try:
            # Verify portfolio exists
            portfolio_check = self.supabase.table("portfolios")\
                .select("id")\
                .eq("id", transaction_data.portfolio_id)\
                .execute()
            
            if not portfolio_check.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio with id '{transaction_data.portfolio_id}' not found"
                )
            
            # Ensure asset exists (database trigger also handles this)
            # This gives us a chance to add metadata if provided
            self.asset_service.get_or_create_asset(transaction_data.symbol)
            
            # Insert transaction
            response = self.supabase.table("transactions")\
                .insert(transaction_data.model_dump())\
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create transaction")
            
            logger.info(f"Created transaction: {transaction_data.symbol} - {transaction_data.transaction_type}")
            
            # After creating transaction, update positions
            self._update_positions(transaction_data.portfolio_id)
            
            return Transaction(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_transactions(
        self,
        portfolio_id: Optional[str] = None,
        symbol: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """
        Get transactions with optional filters.
        
        Args:
            portfolio_id: Filter by portfolio
            symbol: Filter by symbol
            transaction_type: Filter by type (buy, sell, dividend, etc.)
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions
        """
        try:
            query = self.supabase.table("transactions").select("*")
            
            if portfolio_id:
                query = query.eq("portfolio_id", portfolio_id)
            
            if symbol:
                query = query.eq("symbol", symbol.upper())
            
            if transaction_type:
                query = query.eq("transaction_type", transaction_type.lower())
            
            response = query.order("transaction_date", desc=True)\
                .limit(limit)\
                .execute()
            
            return [Transaction(**t) for t in response.data]
            
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_transaction(self, transaction_id: str) -> Transaction:
        """
        Get a specific transaction by ID.
        
        Args:
            transaction_id: Transaction UUID
            
        Returns:
            Transaction object
            
        Raises:
            HTTPException: If transaction not found
        """
        try:
            response = self.supabase.table("transactions")\
                .select("*")\
                .eq("id", transaction_id)\
                .execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Transaction with id '{transaction_id}' not found"
                )
            
            return Transaction(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching transaction: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_transaction(
        self,
        transaction_id: str,
        transaction_data: TransactionUpdate
    ) -> Transaction:
        """
        Update a transaction.
        
        Args:
            transaction_id: Transaction UUID
            transaction_data: Fields to update
            
        Returns:
            Updated transaction
            
        Raises:
            HTTPException: If transaction not found or update fails
        """
        try:
            # Get existing transaction
            existing = self.get_transaction(transaction_id)
            
            # Only include fields that were actually provided
            update_data = transaction_data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # If symbol is being updated, ensure new asset exists
            if "symbol" in update_data:
                self.asset_service.get_or_create_asset(update_data["symbol"])
            
            # Update transaction
            response = self.supabase.table("transactions")\
                .update(update_data)\
                .eq("id", transaction_id)\
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to update transaction")
            
            logger.info(f"Updated transaction: {transaction_id}")
            
            # Recalculate positions after update
            self._update_positions(existing.portfolio_id)
            
            return Transaction(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_transaction(self, transaction_id: str) -> dict:
        """
        Delete a transaction.
        
        Args:
            transaction_id: Transaction UUID
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If transaction not found or deletion fails
        """
        try:
            # Get transaction to get portfolio_id
            transaction = self.get_transaction(transaction_id)
            
            # Delete transaction
            response = self.supabase.table("transactions")\
                .delete()\
                .eq("id", transaction_id)\
                .execute()
            
            logger.info(f"Deleted transaction: {transaction_id}")
            
            # Recalculate positions after deletion
            self._update_positions(transaction.portfolio_id)
            
            return {
                "success": True,
                "message": f"Transaction deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _update_positions(self, portfolio_id: str):
        """
        Recalculate positions for a portfolio based on transactions.
        This is called after any transaction is added, updated, or deleted.
        
        Only processes 'buy' and 'sell' transactions.
        Dividends, splits, etc. are tracked separately.
        
        Args:
            portfolio_id: Portfolio UUID
        """
        try:
            # Get all buy/sell transactions for this portfolio
            transactions = self.supabase.table("transactions")\
                .select("*")\
                .eq("portfolio_id", portfolio_id)\
                .in_("transaction_type", ["buy", "sell"])\
                .order("transaction_date", desc=False)\
                .execute()
            
            # Calculate positions by symbol
            positions = {}
            
            for tx in transactions.data:
                symbol = tx["symbol"]
                quantity = Decimal(str(tx["quantity"])) if tx["quantity"] else Decimal("0")
                price = Decimal(str(tx["price"])) if tx["price"] else Decimal("0")
                fees = Decimal(str(tx.get("fees", 0)))
                tx_type = tx["transaction_type"]
                
                if symbol not in positions:
                    positions[symbol] = {
                        "quantity": Decimal("0"),
                        "total_cost": Decimal("0")
                    }
                
                if tx_type == "buy":
                    # Add to position
                    positions[symbol]["quantity"] += quantity
                    positions[symbol]["total_cost"] += (quantity * price) + fees
                elif tx_type == "sell":
                    # Reduce position
                    if positions[symbol]["quantity"] > 0:
                        # Calculate proportion being sold
                        sell_proportion = quantity / positions[symbol]["quantity"]
                        # Reduce cost basis proportionally
                        cost_reduction = positions[symbol]["total_cost"] * sell_proportion
                        positions[symbol]["total_cost"] -= cost_reduction
                        # Subtract fees from remaining cost
                        positions[symbol]["total_cost"] -= fees
                    positions[symbol]["quantity"] -= quantity
            
            # Delete existing positions for this portfolio
            self.supabase.table("positions")\
                .delete()\
                .eq("portfolio_id", portfolio_id)\
                .execute()
            
            # Insert updated positions (only if quantity > 0)
            for symbol, data in positions.items():
                if data["quantity"] > 0:
                    average_cost = data["total_cost"] / data["quantity"]
                    
                    position_data = {
                        "portfolio_id": portfolio_id,
                        "symbol": symbol,
                        "quantity": float(data["quantity"]),
                        "average_cost": float(average_cost)
                    }
                    
                    self.supabase.table("positions")\
                        .insert(position_data)\
                        .execute()
            
            logger.info(f"Updated positions for portfolio: {portfolio_id}")
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            # Don't raise exception - this is a background operation