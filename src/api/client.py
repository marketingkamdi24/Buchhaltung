"""
API client for fetching data from the Buchhaltung API.
"""
import requests
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, List
from dataclasses import dataclass
import traceback
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import get_config, get_output_path


@dataclass
class APIResponse:
    """Structured response from API calls."""
    success: bool
    message: str
    data: Optional[pd.DataFrame] = None
    file_path: Optional[str] = None


class APIClient:
    """Client for interacting with the Buchhaltung API."""
    
    def __init__(self):
        self.config = get_config().api
    
    def _build_origins(
        self, 
        use_amazon: bool, 
        use_ebay: bool, 
        custom_origins: str
    ) -> Tuple[bool, str, str]:
        """Build the IORIGIN parameter from selected sources."""
        origins = []
        
        if use_amazon:
            origins.append("'Amazon'")
        if use_ebay:
            origins.append("'Ebay'")
        
        # Add custom origins if provided
        if custom_origins and custom_origins.strip():
            custom_list = [
                f"'{item.strip()}'" 
                for item in custom_origins.split(',') 
                if item.strip()
            ]
            origins.extend(custom_list)
        
        if not origins:
            return False, "", "Please select at least one origin (Amazon, Ebay) or provide custom origins."
        
        return True, ','.join(origins), ""
    
    def _parse_response_data(self, data: dict | list) -> Optional[pd.DataFrame]:
        """Parse API response data into a DataFrame."""
        if isinstance(data, dict):
            # Try to find the data array in the response
            if 'data' in data:
                df = pd.DataFrame(data['data'])
            elif 'results' in data:
                df = pd.DataFrame(data['results'])
            elif 'rows' in data:
                df = pd.DataFrame(data['rows'])
            else:
                # If it's a dict with lists, try to convert directly
                df = pd.DataFrame(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            return None
        
        # Check if 'Entries' column exists and expand it
        if 'Entries' in df.columns:
            entries_data = df['Entries'].tolist()
            
            if entries_data and isinstance(entries_data[0], dict):
                df = pd.json_normalize(entries_data)
            elif entries_data and isinstance(entries_data[0], list):
                flattened = []
                for entry in entries_data:
                    if isinstance(entry, list):
                        flattened.extend(entry)
                    else:
                        flattened.append(entry)
                df = pd.json_normalize(flattened)
        
        return df
    
    def fetch_data(
        self,
        date_from: str,
        date_to: str,
        use_amazon: bool = True,
        use_ebay: bool = True,
        custom_origins: str = ""
    ) -> APIResponse:
        """
        Fetch data from the API endpoint.
        
        Args:
            date_from: Start date in DD.MM.YYYY format
            date_to: End date in DD.MM.YYYY format
            use_amazon: Include Amazon as origin
            use_ebay: Include Ebay as origin
            custom_origins: Comma-separated list of custom origins
            
        Returns:
            APIResponse with success status, message, data, and file path
        """
        try:
            # Build origins
            valid, iorigin_value, error_msg = self._build_origins(
                use_amazon, use_ebay, custom_origins
            )
            if not valid:
                return APIResponse(success=False, message=f"❌ Error: {error_msg}")
            
            # Prepare the request
            body = {
                "Parameters": {
                    "IDATE_FROM": date_from,
                    "IDATE_TO": date_to,
                    "IORIGIN": iorigin_value
                }
            }
            
            # Make the request
            response = requests.get(
                self.config.full_url,
                headers=self.config.headers,
                json=body,
                timeout=self.config.timeout
            )
            
            if response.status_code != 200:
                return APIResponse(
                    success=False,
                    message=f"❌ API Error: Status code {response.status_code}\n{response.text}"
                )
            
            # Parse response
            data = response.json()
            df = self._parse_response_data(data)
            
            if df is None:
                return APIResponse(
                    success=False,
                    message="❌ Unexpected data format received from API"
                )
            
            if df.empty:
                return APIResponse(
                    success=False,
                    message="⚠️ Warning: API returned empty data"
                )
            
            # Save to Excel file
            output_filename = f"api_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_path = get_output_path(output_filename)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            result_message = f"""✅ Data fetched successfully!

📊 **Summary:**
- Total rows: {len(df)}
- Total columns: {len(df.columns)}
- Date range: {date_from} to {date_to}
- Origins: {iorigin_value}

🔑 **Key Column:** ORDER_ID (for matching in Step 2)

💾 File saved as: {output_filename}

You can now proceed to match this data with your shop data or process it directly."""
            
            return APIResponse(
                success=True,
                message=result_message,
                data=df,
                file_path=str(output_path)
            )
            
        except requests.exceptions.Timeout:
            return APIResponse(
                success=False,
                message="❌ Error: Request timed out. Please try again."
            )
        except requests.exceptions.ConnectionError:
            return APIResponse(
                success=False,
                message="❌ Error: Could not connect to the API. Please check the URL and your internet connection."
            )
        except Exception as e:
            return APIResponse(
                success=False,
                message=f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            )


# Convenience function for backward compatibility
def fetch_data_from_api(
    date_from: str,
    date_to: str,
    use_amazon: bool,
    use_ebay: bool,
    custom_origins: str
) -> Tuple[str, Optional[pd.DataFrame], Optional[str]]:
    """
    Fetch data from API (convenience function).
    
    Returns:
        Tuple of (message, dataframe, file_path)
    """
    client = APIClient()
    response = client.fetch_data(date_from, date_to, use_amazon, use_ebay, custom_origins)
    return response.message, response.data, response.file_path