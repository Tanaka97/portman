"""
Portfolio service - handles all portfolio-related business logic.
Updated to work with user_id and new schema.
"""

from app.database import get_supabase_client
from app.models.schemas import PortfolioCreate, PortfolioUpdate, Portfolio
from app.config import TEST_USER_ID
from typing import List, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service class for portfolio operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def create_portfolio(self, portfolio_data: PortfolioCreate, user_id: Optional[str] = None) -> Portfolio:
        """
        Create a new portfolio.
        
        Args:
            portfolio_data: Portfolio creation data
            user_id: User ID (optional, defaults to TEST_USER_ID for now)
            
        Returns:
            Created portfolio
            
        Raises:
            HTTPException: If portfolio name already exists or creation fails
        """
        try:
            # Use test user ID for now (Phase 2 will use real auth)
            if user_id is None:
                user_id = TEST_USER_ID
            
            # Check if portfolio with same name exists for this user
            existing = self.supabase.table("portfolios")\
                .select("id")\
                .eq("name", portfolio_data.name)\
                .eq("user_id", user_id)\
                .execute()
            
            if existing.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Portfolio with name '{portfolio_data.name}' already exists"
                )
            
            # Prepare data with user_id
            insert_data = portfolio_data.model_dump()
            insert_data["user_id"] = user_id
            
            # Insert new portfolio
            response = self.supabase.table("portfolios")\
                .insert(insert_data)\
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to create portfolio")
            
            logger.info(f"Created portfolio: {portfolio_data.name} for user: {user_id}")
            return Portfolio(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_portfolios(self, user_id: Optional[str] = None) -> List[Portfolio]:
        """
        Get all portfolios for a user.
        
        Args:
            user_id: User ID (optional, defaults to TEST_USER_ID)
            
        Returns:
            List of all portfolios
        """
        try:
            if user_id is None:
                user_id = TEST_USER_ID
            
            response = self.supabase.table("portfolios")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return [Portfolio(**p) for p in response.data]
            
        except Exception as e:
            logger.error(f"Error fetching portfolios: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_portfolio(self, portfolio_id: str, user_id: Optional[str] = None) -> Portfolio:
        """
        Get a specific portfolio by ID.
        
        Args:
            portfolio_id: Portfolio UUID
            user_id: User ID (optional, defaults to TEST_USER_ID)
            
        Returns:
            Portfolio object
            
        Raises:
            HTTPException: If portfolio not found
        """
        try:
            if user_id is None:
                user_id = TEST_USER_ID
            
            response = self.supabase.table("portfolios")\
                .select("*")\
                .eq("id", portfolio_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Portfolio with id '{portfolio_id}' not found"
                )
            
            return Portfolio(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_portfolio(
        self,
        portfolio_id: str,
        portfolio_data: PortfolioUpdate,
        user_id: Optional[str] = None
    ) -> Portfolio:
        """
        Update a portfolio.
        
        Args:
            portfolio_id: Portfolio UUID
            portfolio_data: Fields to update
            user_id: User ID (optional, defaults to TEST_USER_ID)
            
        Returns:
            Updated portfolio
            
        Raises:
            HTTPException: If portfolio not found or update fails
        """
        try:
            if user_id is None:
                user_id = TEST_USER_ID
            
            # Check portfolio exists and belongs to user
            self.get_portfolio(portfolio_id, user_id)
            
            # Only include fields that were actually provided
            update_data = portfolio_data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # Check for name conflicts if name is being updated
            if "name" in update_data:
                existing = self.supabase.table("portfolios")\
                    .select("id")\
                    .eq("name", update_data["name"])\
                    .eq("user_id", user_id)\
                    .neq("id", portfolio_id)\
                    .execute()
                
                if existing.data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Portfolio with name '{update_data['name']}' already exists"
                    )
            
            # Update portfolio
            response = self.supabase.table("portfolios")\
                .update(update_data)\
                .eq("id", portfolio_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to update portfolio")
            
            logger.info(f"Updated portfolio: {portfolio_id}")
            return Portfolio(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def delete_portfolio(self, portfolio_id: str, user_id: Optional[str] = None) -> dict:
        """
        Delete a portfolio and all associated data.
        
        Args:
            portfolio_id: Portfolio UUID
            user_id: User ID (optional, defaults to TEST_USER_ID)
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If portfolio not found or deletion fails
        """
        try:
            if user_id is None:
                user_id = TEST_USER_ID
            
            # Check portfolio exists and belongs to user
            portfolio = self.get_portfolio(portfolio_id, user_id)
            
            # Delete portfolio (CASCADE will delete related data)
            response = self.supabase.table("portfolios")\
                .delete()\
                .eq("id", portfolio_id)\
                .eq("user_id", user_id)\
                .execute()
            
            logger.info(f"Deleted portfolio: {portfolio.name}")
            return {
                "success": True,
                "message": f"Portfolio '{portfolio.name}' deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))