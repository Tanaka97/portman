"""
CSV Import Service - handles bulk transaction imports from brokers.
Updated to work with new schema and asset table.
"""

import csv
import io
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.schemas import TransactionCreate, CSVImportResponse, CSVImportRequest
from app.services.transaction_service import TransactionService
from app.services.asset_service import AssetService
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class CSVImportService:
    """Service for importing transactions from CSV files"""
    
    def __init__(self):
        self.transaction_service = TransactionService()
        self.asset_service = AssetService()
    
    def import_transactions(self, request: CSVImportRequest) -> CSVImportResponse:
        """
        Import transactions from CSV data.
        
        Args:
            request: CSV import request with data and broker format
            
        Returns:
            Import results with counts and errors
        """
        try:
            logger.info(f"Starting CSV import for portfolio: {request.portfolio_id}")
            
            # Parse CSV data
            csv_reader = csv.DictReader(io.StringIO(request.csv_data))
            rows = list(csv_reader)
            
            if not rows:
                raise HTTPException(status_code=400, detail="CSV file is empty")
            
            logger.info(f"Processing {len(rows)} CSV rows")
            
            # Import based on broker format
            if request.broker_format.lower() == "robinhood":
                return self._import_robinhood(request.portfolio_id, rows)
            elif request.broker_format.lower() == "interactivebrokers":
                return self._import_ibkr(request.portfolio_id, rows)
            elif request.broker_format.lower() == "generic":
                return self._import_generic(request.portfolio_id, rows)
            else:
                # Default to generic format
                return self._import_generic(request.portfolio_id, rows)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CSV import error: {e}")
            raise HTTPException(status_code=500, detail=f"CSV import failed: {str(e)}")
    
    def _import_robinhood(self, portfolio_id: str, rows: List[Dict[str, Any]]) -> CSVImportResponse:
        """
        Import Robinhood CSV format.
        
        Expected columns:
        - Activity Date
        - Process Date  
        - Settlement Date
        - Instrument
        - Symbol
        - Description
        - Activity Type
        - Quantity
        - Price
        - Amount
        """
        imported = []
        errors = []
        
        for i, row in enumerate(rows, 1):
            try:
                # Skip non-transaction rows
                activity_type = row.get("Activity Type", "").lower()
                if activity_type not in ["buy", "sell"]:
                    continue
                
                # Parse data
                symbol = row.get("Symbol", "").upper().strip()
                if not symbol:
                    errors.append(f"Row {i}: Missing symbol")
                    continue
                
                transaction_type = activity_type
                quantity = abs(float(row.get("Quantity", 0)))
                price = abs(float(row.get("Price", 0)))
                
                # Robinhood uses negative amounts for sells
                amount = float(row.get("Amount", 0))
                fees = 0  # Robinhood doesn't show fees in standard export
                
                # Parse date - try multiple formats
                date_str = row.get("Activity Date", row.get("Process Date", ""))
                transaction_date = self._parse_date(date_str)
                
                # Create transaction
                transaction = TransactionCreate(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    fees=fees,
                    transaction_date=transaction_date,
                    notes=f"Imported from Robinhood: {row.get('Description', '')}"
                )
                
                # Create in database
                created = self.transaction_service.create_transaction(transaction)
                imported.append(created)
                
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
                logger.warning(f"Row {i} import failed: {e}")
        
        return CSVImportResponse(
            success=True,
            imported_count=len(imported),
            failed_count=len(errors),
            errors=errors,
            transactions=imported
        )
    
    def _import_ibkr(self, portfolio_id: str, rows: List[Dict[str, Any]]) -> CSVImportResponse:
        """
        Import Interactive Brokers CSV format.
        
        Expected columns:
        - TradeDate
        - SettleDate  
        - Currency
        - Description
        - Symbol
        - Quantity
        - Price
        - Amount
        - Fees
        """
        imported = []
        errors = []
        
        for i, row in enumerate(rows, 1):
            try:
                # Skip header rows
                if "header" in str(row).lower():
                    continue
                
                # Parse transaction type from description
                description = row.get("Description", "").lower()
                if "buy" in description:
                    transaction_type = "buy"
                elif "sell" in description:
                    transaction_type = "sell"
                else:
                    continue  # Skip non-transaction rows
                
                symbol = row.get("Symbol", "").upper().strip()
                if not symbol:
                    errors.append(f"Row {i}: Missing symbol")
                    continue
                
                quantity = abs(float(row.get("Quantity", 0)))
                price = abs(float(row.get("Price", 0)))
                fees = abs(float(row.get("Fees", 0)))
                
                # Parse date
                date_str = row.get("TradeDate", "")
                transaction_date = self._parse_date(date_str)
                
                # Create transaction
                transaction = TransactionCreate(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    fees=fees,
                    transaction_date=transaction_date,
                    notes=f"Imported from IBKR: {row.get('Description', '')}"
                )
                
                created = self.transaction_service.create_transaction(transaction)
                imported.append(created)
                
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
        
        return CSVImportResponse(
            success=True,
            imported_count=len(imported),
            failed_count=len(errors),
            errors=errors,
            transactions=imported
        )
    
    def _import_generic(self, portfolio_id: str, rows: List[Dict[str, Any]]) -> CSVImportResponse:
        """
        Import generic CSV format.
        
        Expected columns (flexible mapping):
        - date, symbol, type, quantity, price, fees (optional)
        - OR: Date, Symbol, Type, Quantity, Price, Fees (optional)
        """
        imported = []
        errors = []
        
        # Column name mapping (case-insensitive)
        column_map = {
            "date": None,
            "symbol": None,
            "type": None,
            "quantity": None,
            "price": None,
            "fees": None
        }
        
        # Auto-detect column names from first row
        if rows:
            first_row = {k.lower(): v for k, v in rows[0].items()}
            for key in column_map:
                for col in first_row.keys():
                    if key in col.lower():
                        column_map[key] = col
                        break
        
        for i, row in enumerate(rows, 1):
            try:
                # Get values using mapped column names
                row_lower = {k.lower(): v for k, v in row.items()}
                
                symbol = self._get_value(row, column_map, "symbol")
                if not symbol:
                    errors.append(f"Row {i}: Missing symbol")
                    continue
                
                transaction_type = self._get_value(row, column_map, "type", "").lower()
                if transaction_type not in ["buy", "sell"]:
                    errors.append(f"Row {i}: Invalid transaction type '{transaction_type}'")
                    continue
                
                quantity = float(self._get_value(row, column_map, "quantity", 0))
                price = float(self._get_value(row, column_map, "price", 0))
                fees = float(self._get_value(row, column_map, "fees", 0))
                
                date_str = self._get_value(row, column_map, "date")
                transaction_date = self._parse_date(date_str)
                
                # Create transaction
                transaction = TransactionCreate(
                    portfolio_id=portfolio_id,
                    symbol=symbol.upper(),
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    fees=fees,
                    transaction_date=transaction_date,
                    notes=f"Imported from CSV row {i}"
                )
                
                created = self.transaction_service.create_transaction(transaction)
                imported.append(created)
                
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
        
        return CSVImportResponse(
            success=True,
            imported_count=len(imported),
            failed_count=len(errors),
            errors=errors,
            transactions=imported
        )
    
    def _get_value(self, row: Dict[str, Any], column_map: Dict[str, str], key: str, default=None):
        """Get value from row using column mapping"""
        col_name = column_map.get(key)
        if col_name and col_name in row:
            return row[col_name]
        
        # Try case-insensitive lookup
        row_lower = {k.lower(): v for k, v in row.items()}
        for k, v in row_lower.items():
            if key in k:
                return v
        
        return default
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in various formats"""
        if not date_str:
            return datetime.now()
        
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%m/%d/%Y %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        # If no format matches, return current date
        logger.warning(f"Could not parse date: {date_str}, using current date")
        return datetime.now()