"""
Asset service - handles asset (stocks, crypto, etc.) management.
Assets are stored in a separate lookup table for metadata like sector, industry, etc.
"""

from app.database import get_supabase_client
from app.models.schemas import AssetCreate, AssetUpdate, Asset
from typing import List, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class AssetService:
    """Service class for asset operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_or_create_asset(self, ticker: str, asset_data: Optional[AssetCreate] = None) -> Asset:
        """
        Get an existing asset or create a minimal one if it doesn't exist.
        
        This is called automatically when transactions are created.
        The database trigger also handles this, but we do it here too for consistency.
        
        Args:
            ticker: Stock/crypto ticker symbol
            asset_data: Optional full asset data
            
        Returns:
            Asset object
        """
        try:
            ticker = ticker.upper().strip()
            
            # Try to get existing asset
            response = self.supabase.table("assets")\
                .select("*")\
                .eq("ticker", ticker)\
                .execute()
            
            if response.data:
                return Asset(**response.data[0])
            
            # Asset doesn't exist, create it
            if asset_data:
                # Use provided data
                insert_data = asset_data.model_dump()
                insert_data["ticker"] = ticker
            else:
                # Create minimal asset
                insert_data = {"ticker": ticker}
            
            create_response = self.supabase.table("assets")\
                .insert(insert_data)\
                .execute()
            
            if not create_response.data:
                raise HTTPException(status_code=500, detail=f"Failed to create asset: {ticker}")
            
            logger.info(f"Created new asset: {ticker}")
            return Asset(**create_response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_or_create_asset: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_asset(self, ticker: str) -> Asset:
        """
        Get an asset by ticker symbol.
        
        Args:
            ticker: Stock/crypto ticker
            
        Returns:
            Asset object
            
        Raises:
            HTTPException: If asset not found
        """
        try:
            ticker = ticker.upper().strip()
            
            response = self.supabase.table("assets")\
                .select("*")\
                .eq("ticker", ticker)\
                .execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Asset '{ticker}' not found"
                )
            
            return Asset(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching asset: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_assets(self, limit: int = 1000) -> List[Asset]:
        """
        Get all assets.
        
        Args:
            limit: Maximum number of assets to return
            
        Returns:
            List of assets
        """
        try:
            response = self.supabase.table("assets")\
                .select("*")\
                .order("ticker")\
                .limit(limit)\
                .execute()
            
            return [Asset(**a) for a in response.data]
            
        except Exception as e:
            logger.error(f"Error fetching assets: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def update_asset(self, ticker: str, asset_data: AssetUpdate) -> Asset:
        """
        Update asset metadata.
        
        Args:
            ticker: Asset ticker symbol
            asset_data: Fields to update
            
        Returns:
            Updated asset
            
        Raises:
            HTTPException: If asset not found or update fails
        """
        try:
            ticker = ticker.upper().strip()
            
            # Check asset exists
            self.get_asset(ticker)
            
            # Only include fields that were provided
            update_data = asset_data.model_dump(exclude_unset=True)
            
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            # Update asset
            response = self.supabase.table("assets")\
                .update(update_data)\
                .eq("ticker", ticker)\
                .execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Failed to update asset")
            
            logger.info(f"Updated asset: {ticker}")
            return Asset(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating asset: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def search_assets(self, query: str) -> List[Asset]:
        """
        Search assets by ticker or name.
        
        Args:
            query: Search query
            
        Returns:
            List of matching assets
        """
        try:
            query = query.upper().strip()
            
            # Search by ticker or name (case-insensitive)
            response = self.supabase.table("assets")\
                .select("*")\
                .or_(f"ticker.ilike.%{query}%,name.ilike.%{query}%")\
                .limit(50)\
                .execute()
            
            return [Asset(**a) for a in response.data]
            
        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            raise HTTPException(status_code=500, detail=str(e))