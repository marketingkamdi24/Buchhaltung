"""
Data matcher module.
Matches shop data with API data and processes the matched Excel file.
"""
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import get_config, get_output_path
from src.processors.excel_processor import ExcelProcessor


@dataclass
class MatchResult:
    success: bool
    message: str
    data: Optional[pd.DataFrame] = None
    file_path: Optional[str] = None
    matched_file_path: Optional[str] = None
    processed_file_path: Optional[str] = None


class DataMatcher:
    """Matches shop data with API data and processes the result."""
    
    def __init__(self):
        self.config = get_config().excel
    
    def match_and_process(self, api_data: pd.DataFrame, shop_file_path: str) -> MatchResult:
        """
        Match shop data with API data and process the matched Excel file.
        
        This combines the matching step and processing step into one:
        1. Filter shop data to only include rows where Bestellnummer matches ORDER_ID from API
        2. Save the matched data to an intermediate file
        3. Process the matched file using ExcelProcessor with KD-NR/RG-NR mapping from API data
        
        Args:
            api_data: DataFrame containing API data with ORDER_ID, KUNDENNR, BELEGNR columns
            shop_file_path: Path to the shop Excel file
        
        Returns:
            MatchResult with success status, message, matched data, and file paths
        """
        results = []
        
        try:
            # Validate API data
            if api_data is None or api_data.empty:
                return MatchResult(
                    success=False,
                    message="❌ Error: Fetch API data first (Step 1)"
                )
            
            if self.config.api_order_column not in api_data.columns:
                return MatchResult(
                    success=False,
                    message=f"❌ Error: {self.config.api_order_column} column not found in API data"
                )
            
            # Load shop file
            results.append(f"📄 Loading shop file: {os.path.basename(shop_file_path)}")
            try:
                shop_df = pd.read_excel(
                    shop_file_path,
                    engine='openpyxl',
                    header=self.config.shop_data_header_row
                )
                results.append(f"✅ Loaded {len(shop_df)} rows from shop file")
            except Exception as e:
                return MatchResult(
                    success=False,
                    message=f"❌ Error loading shop file: {e}"
                )
            
            # Check for Bestellnummer column
            if self.config.shop_order_column not in shop_df.columns:
                return MatchResult(
                    success=False,
                    message=f"❌ Error: {self.config.shop_order_column} column not found in shop data"
                )
            
            # Get API order IDs for matching
            api_order_ids = api_data[self.config.api_order_column].dropna().unique().tolist()
            results.append(f"✅ Found {len(api_order_ids)} unique ORDER_IDs from API data")
            
            # Match shop data by Bestellnummer
            matched_df = shop_df[shop_df[self.config.shop_order_column].isin(api_order_ids)]
            
            if matched_df.empty:
                return MatchResult(
                    success=False,
                    message="❌ Error: No matching orders found between API data and shop file"
                )
            
            match_count = len(matched_df)
            total_count = len(shop_df)
            results.append(f"✅ Matched {match_count} of {total_count} rows ({100*match_count/total_count:.1f}%)")
            
            # Save matched data to intermediate file (original format for reference)
            matched_filename = f"matched_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            matched_path = get_output_path(matched_filename)
            matched_df.to_excel(matched_path, index=False, engine='openpyxl')
            results.append(f"✅ Saved matched data to: {matched_filename}")
            
            # Now process the original shop file with the ExcelProcessor
            # The processor will use the API data for KD-NR/RG-NR mapping
            results.append("\n📊 Processing matched Excel file...")
            results.append("-" * 50)
            
            processor = ExcelProcessor()
            process_result = processor.process(shop_file_path, api_data)
            
            # Append processor results
            results.append(process_result.message)
            
            if process_result.success:
                return MatchResult(
                    success=True,
                    message="\n".join(results),
                    data=matched_df,
                    file_path=str(process_result.file_path),  # Main output is processed file
                    matched_file_path=str(matched_path),
                    processed_file_path=str(process_result.file_path)
                )
            else:
                return MatchResult(
                    success=False,
                    message="\n".join(results),
                    data=matched_df,
                    matched_file_path=str(matched_path)
                )
            
        except Exception as e:
            import traceback
            return MatchResult(
                success=False,
                message=f"❌ Error: {e}\n{traceback.format_exc()}"
            )
    
    def match_data(self, api_data: pd.DataFrame, shop_file_path: str) -> MatchResult:
        """
        Match shop data with API data (legacy method, now calls match_and_process).
        
        Args:
            api_data: DataFrame containing API data
            shop_file_path: Path to the shop Excel file
        
        Returns:
            MatchResult with success status and file paths
        """
        return self.match_and_process(api_data, shop_file_path)


def match_belegnr_data(api_data_df, shop_file):
    """
    Wrapper function for Gradio interface.
    Matches shop data and processes the Excel file.
    
    Returns:
        Tuple of (message, data, processed_file_path)
    """
    if shop_file is None:
        return "❌ Error: Upload shop file", None, None
    
    matcher = DataMatcher()
    file_path = shop_file.name if hasattr(shop_file, 'name') else str(shop_file)
    result = matcher.match_and_process(api_data_df, file_path)
    
    return result.message, result.data, result.file_path
