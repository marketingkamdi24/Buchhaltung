"""
Data Analysis module for sales data analytics.
Provides comprehensive analysis functions for multi-platform sales data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@dataclass
class AnalysisResult:
    """Structured result from analysis operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    charts: Optional[Dict[str, Any]] = None


class DataAnalyzer:
    """Comprehensive data analyzer for sales data."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize analyzer with DataFrame."""
        self.df = df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare and clean data for analysis."""
        # Convert date columns to datetime
        date_columns = ['BELEGDAT', 'LIEFERDAT']
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = ['NETTO', 'BRUTTO', 'ERLOES']
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Clean ORIGIN column
        if 'ORIGIN' in self.df.columns:
            self.df['ORIGIN'] = self.df['ORIGIN'].fillna('Unknown').str.strip()
        
        # Clean country codes
        if 'ISOA2_LAND' in self.df.columns:
            self.df['ISOA2_LAND'] = self.df['ISOA2_LAND'].fillna('Unknown').str.strip()
        
        # Add derived columns
        if 'BELEGDAT' in self.df.columns:
            self.df['Date'] = self.df['BELEGDAT'].dt.date
            self.df['Month'] = self.df['BELEGDAT'].dt.to_period('M')
            self.df['Week'] = self.df['BELEGDAT'].dt.to_period('W')
            self.df['DayOfWeek'] = self.df['BELEGDAT'].dt.day_name()
            self.df['Hour'] = self.df['BELEGDAT'].dt.hour
    
    def get_kpi_metrics(self) -> Dict[str, Any]:
        """Calculate key performance indicators."""
        metrics = {}
        
        # Total revenue metrics
        if 'BRUTTO' in self.df.columns:
            metrics['total_gross_revenue'] = self.df['BRUTTO'].sum()
            metrics['avg_order_value_gross'] = self.df['BRUTTO'].mean()
            metrics['max_order_gross'] = self.df['BRUTTO'].max()
            metrics['min_order_gross'] = self.df['BRUTTO'].min()
        
        if 'NETTO' in self.df.columns:
            metrics['total_net_revenue'] = self.df['NETTO'].sum()
            metrics['avg_order_value_net'] = self.df['NETTO'].mean()
        
        if 'ERLOES' in self.df.columns:
            metrics['total_profit'] = self.df['ERLOES'].sum()
            metrics['avg_profit_per_order'] = self.df['ERLOES'].mean()
        
        # Order counts
        metrics['total_orders'] = len(self.df)
        
        if 'KUNDENNR' in self.df.columns:
            metrics['unique_customers'] = self.df['KUNDENNR'].nunique()
            metrics['orders_per_customer'] = metrics['total_orders'] / max(metrics['unique_customers'], 1)
        
        # Platform breakdown
        if 'ORIGIN' in self.df.columns:
            metrics['platforms'] = self.df['ORIGIN'].nunique()
        
        # Country breakdown
        if 'ISOA2_LAND' in self.df.columns:
            metrics['countries'] = self.df['ISOA2_LAND'].nunique()
        
        # Date range
        if 'BELEGDAT' in self.df.columns:
            metrics['date_range_start'] = self.df['BELEGDAT'].min()
            metrics['date_range_end'] = self.df['BELEGDAT'].max()
            if pd.notna(metrics['date_range_start']) and pd.notna(metrics['date_range_end']):
                metrics['days_span'] = (metrics['date_range_end'] - metrics['date_range_start']).days + 1
                metrics['avg_orders_per_day'] = metrics['total_orders'] / max(metrics['days_span'], 1)
        
        # Profit margin
        if 'BRUTTO' in self.df.columns and 'ERLOES' in self.df.columns:
            total_brutto = self.df['BRUTTO'].sum()
            if total_brutto > 0:
                metrics['profit_margin_pct'] = (self.df['ERLOES'].sum() / total_brutto) * 100
        
        return metrics
    
    def get_platform_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze sales by platform (Amazon, eBay, etc.)."""
        results = {}
        
        if 'ORIGIN' not in self.df.columns:
            return results
        
        # Revenue by platform
        agg_cols = {}
        if 'BRUTTO' in self.df.columns:
            agg_cols['BRUTTO'] = ['sum', 'mean', 'count']
        if 'NETTO' in self.df.columns:
            agg_cols['NETTO'] = ['sum', 'mean']
        if 'ERLOES' in self.df.columns:
            agg_cols['ERLOES'] = ['sum', 'mean']
        
        if agg_cols:
            platform_stats = self.df.groupby('ORIGIN').agg(agg_cols)
            platform_stats.columns = ['_'.join(col).strip() for col in platform_stats.columns.values]
            platform_stats = platform_stats.reset_index()
            results['platform_summary'] = platform_stats
        
        # Platform share
        if 'BRUTTO' in self.df.columns:
            platform_revenue = self.df.groupby('ORIGIN')['BRUTTO'].sum().reset_index()
            platform_revenue['percentage'] = (platform_revenue['BRUTTO'] / platform_revenue['BRUTTO'].sum()) * 100
            results['platform_share'] = platform_revenue
        
        # Order count by platform
        platform_orders = self.df.groupby('ORIGIN').size().reset_index(name='order_count')
        platform_orders['percentage'] = (platform_orders['order_count'] / platform_orders['order_count'].sum()) * 100
        results['platform_orders'] = platform_orders
        
        return results
    
    def get_geographic_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze sales by country/region."""
        results = {}
        
        if 'ISOA2_LAND' not in self.df.columns:
            return results
        
        # Revenue by country
        country_cols = {}
        if 'BRUTTO' in self.df.columns:
            country_cols['BRUTTO'] = ['sum', 'mean', 'count']
        if 'NETTO' in self.df.columns:
            country_cols['NETTO'] = ['sum', 'mean']
        if 'ERLOES' in self.df.columns:
            country_cols['ERLOES'] = ['sum', 'mean']
        
        if country_cols:
            country_stats = self.df.groupby('ISOA2_LAND').agg(country_cols)
            country_stats.columns = ['_'.join(col).strip() for col in country_stats.columns.values]
            country_stats = country_stats.reset_index()
            country_stats = country_stats.sort_values('BRUTTO_sum', ascending=False)
            results['country_summary'] = country_stats
        
        # Country share
        if 'BRUTTO' in self.df.columns:
            country_revenue = self.df.groupby('ISOA2_LAND')['BRUTTO'].sum().reset_index()
            country_revenue['percentage'] = (country_revenue['BRUTTO'] / country_revenue['BRUTTO'].sum()) * 100
            country_revenue = country_revenue.sort_values('BRUTTO', ascending=False)
            results['country_share'] = country_revenue
        
        # Orders by country
        country_orders = self.df.groupby('ISOA2_LAND').size().reset_index(name='order_count')
        country_orders['percentage'] = (country_orders['order_count'] / country_orders['order_count'].sum()) * 100
        country_orders = country_orders.sort_values('order_count', ascending=False)
        results['country_orders'] = country_orders
        
        # Country by platform
        if 'ORIGIN' in self.df.columns and 'BRUTTO' in self.df.columns:
            country_platform = self.df.groupby(['ISOA2_LAND', 'ORIGIN'])['BRUTTO'].sum().reset_index()
            country_platform = country_platform.pivot(index='ISOA2_LAND', columns='ORIGIN', values='BRUTTO').fillna(0)
            results['country_platform_matrix'] = country_platform.reset_index()
        
        return results
    
    def get_time_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze sales over time (daily, weekly, monthly trends)."""
        results = {}
        
        if 'BELEGDAT' not in self.df.columns:
            return results
        
        # Daily trends
        if 'Date' in self.df.columns:
            daily_cols = {}
            if 'BRUTTO' in self.df.columns:
                daily_cols['BRUTTO'] = 'sum'
            if 'NETTO' in self.df.columns:
                daily_cols['NETTO'] = 'sum'
            if 'ERLOES' in self.df.columns:
                daily_cols['ERLOES'] = 'sum'
            
            if daily_cols:
                daily_cols['BELEGDAT'] = 'count'
                daily_stats = self.df.groupby('Date').agg(daily_cols).reset_index()
                daily_stats.columns = ['Date', 'Gross_Revenue', 'Net_Revenue', 'Profit', 'Order_Count'] if len(daily_cols) == 4 else daily_stats.columns
                results['daily_trend'] = daily_stats
        
        # Weekly trends
        if 'Week' in self.df.columns:
            weekly_cols = {}
            if 'BRUTTO' in self.df.columns:
                weekly_cols['BRUTTO'] = 'sum'
            if 'ERLOES' in self.df.columns:
                weekly_cols['ERLOES'] = 'sum'
            
            if weekly_cols:
                weekly_cols['BELEGDAT'] = 'count'
                weekly_stats = self.df.groupby('Week').agg(weekly_cols).reset_index()
                weekly_stats['Week'] = weekly_stats['Week'].astype(str)
                results['weekly_trend'] = weekly_stats
        
        # Monthly trends
        if 'Month' in self.df.columns:
            monthly_cols = {}
            if 'BRUTTO' in self.df.columns:
                monthly_cols['BRUTTO'] = 'sum'
            if 'ERLOES' in self.df.columns:
                monthly_cols['ERLOES'] = 'sum'
            
            if monthly_cols:
                monthly_cols['BELEGDAT'] = 'count'
                monthly_stats = self.df.groupby('Month').agg(monthly_cols).reset_index()
                monthly_stats['Month'] = monthly_stats['Month'].astype(str)
                results['monthly_trend'] = monthly_stats
        
        # Day of week analysis
        if 'DayOfWeek' in self.df.columns and 'BRUTTO' in self.df.columns:
            dow_stats = self.df.groupby('DayOfWeek').agg({
                'BRUTTO': ['sum', 'mean', 'count']
            }).reset_index()
            dow_stats.columns = ['DayOfWeek', 'Total_Revenue', 'Avg_Revenue', 'Order_Count']
            # Sort by day of week
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_stats['DayOfWeek'] = pd.Categorical(dow_stats['DayOfWeek'], categories=day_order, ordered=True)
            dow_stats = dow_stats.sort_values('DayOfWeek')
            results['day_of_week'] = dow_stats
        
        # Hourly pattern
        if 'Hour' in self.df.columns and 'BRUTTO' in self.df.columns:
            hourly_stats = self.df.groupby('Hour').agg({
                'BRUTTO': ['sum', 'count']
            }).reset_index()
            hourly_stats.columns = ['Hour', 'Total_Revenue', 'Order_Count']
            results['hourly_pattern'] = hourly_stats
        
        return results
    
    def get_customer_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze customer behavior and top customers."""
        results = {}
        
        if 'KUNDENNR' not in self.df.columns:
            return results
        
        # Top customers by revenue
        customer_cols = {}
        if 'BRUTTO' in self.df.columns:
            customer_cols['BRUTTO'] = 'sum'
        if 'ERLOES' in self.df.columns:
            customer_cols['ERLOES'] = 'sum'
        
        if customer_cols:
            customer_cols['BELEGNR'] = 'count'
            
            # Include name if available
            name_col = 'NAME2' if 'NAME2' in self.df.columns else ('NAME1' if 'NAME1' in self.df.columns else None)
            if name_col:
                customer_stats = self.df.groupby(['KUNDENNR', name_col]).agg(customer_cols).reset_index()
                customer_stats.columns = ['Customer_ID', 'Customer_Name', 'Total_Revenue', 'Total_Profit', 'Order_Count'] if 'ERLOES' in customer_cols else ['Customer_ID', 'Customer_Name', 'Total_Revenue', 'Order_Count']
            else:
                customer_stats = self.df.groupby('KUNDENNR').agg(customer_cols).reset_index()
                customer_stats.columns = ['Customer_ID', 'Total_Revenue', 'Total_Profit', 'Order_Count'] if 'ERLOES' in customer_cols else ['Customer_ID', 'Total_Revenue', 'Order_Count']
            
            customer_stats = customer_stats.sort_values('Total_Revenue', ascending=False)
            results['top_customers'] = customer_stats.head(20)
            results['all_customers'] = customer_stats
        
        # Customer frequency distribution
        if 'BRUTTO' in self.df.columns:
            customer_orders = self.df.groupby('KUNDENNR').size().reset_index(name='order_count')
            
            # Categorize customers
            def categorize_customer(orders):
                if orders == 1:
                    return 'One-time'
                elif orders <= 3:
                    return 'Occasional (2-3)'
                elif orders <= 10:
                    return 'Regular (4-10)'
                else:
                    return 'Loyal (10+)'
            
            customer_orders['category'] = customer_orders['order_count'].apply(categorize_customer)
            frequency_dist = customer_orders.groupby('category').agg({
                'KUNDENNR': 'count',
                'order_count': 'sum'
            }).reset_index()
            frequency_dist.columns = ['Category', 'Customer_Count', 'Total_Orders']
            results['customer_frequency'] = frequency_dist
        
        # New vs returning customers by date
        if 'BELEGDAT' in self.df.columns and 'Date' in self.df.columns:
            # Sort by date and find first order for each customer
            sorted_df = self.df.sort_values('BELEGDAT')
            first_orders = sorted_df.groupby('KUNDENNR')['Date'].first().reset_index()
            first_orders.columns = ['KUNDENNR', 'first_order_date']
            
            # Merge back to get new vs returning for each order
            merged = self.df.merge(first_orders, on='KUNDENNR')
            merged['is_new_customer'] = merged['Date'] == merged['first_order_date']
            
            # Aggregate by date
            new_returning = merged.groupby(['Date', 'is_new_customer']).size().unstack(fill_value=0).reset_index()
            if True in new_returning.columns and False in new_returning.columns:
                new_returning.columns = ['Date', 'Returning', 'New']
            results['new_vs_returning'] = new_returning
        
        return results
    
    def get_document_type_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze by document type (RE, GU, etc.)."""
        results = {}
        
        if 'BELEGART' not in self.df.columns:
            return results
        
        # Document type breakdown
        doc_cols = {}
        if 'BRUTTO' in self.df.columns:
            doc_cols['BRUTTO'] = 'sum'
        if 'NETTO' in self.df.columns:
            doc_cols['NETTO'] = 'sum'
        if 'ERLOES' in self.df.columns:
            doc_cols['ERLOES'] = 'sum'
        
        if doc_cols:
            doc_cols['BELEGNR'] = 'count'
            doc_stats = self.df.groupby('BELEGART').agg(doc_cols).reset_index()
            doc_stats.columns = ['Document_Type', 'Gross_Revenue', 'Net_Revenue', 'Profit', 'Count'] if len(doc_cols) == 4 else doc_stats.columns
            results['document_type_summary'] = doc_stats
        
        # Document type names mapping
        doc_type_names = {
            'RE': 'Invoice (Rechnung)',
            'GU': 'Credit Note (Gutschrift)',
            'V': 'Sale (Verkauf)'
        }
        
        return results
    
    def get_profitability_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze profitability metrics."""
        results = {}
        
        if 'ERLOES' not in self.df.columns or 'BRUTTO' not in self.df.columns:
            return results
        
        # Calculate profit margin for each order
        df_profit = self.df.copy()
        df_profit['profit_margin'] = (df_profit['ERLOES'] / df_profit['BRUTTO'].replace(0, np.nan)) * 100
        
        # Profit margin distribution
        bins = [-np.inf, 0, 10, 20, 30, 40, 50, np.inf]
        labels = ['Negative', '0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50%+']
        df_profit['margin_category'] = pd.cut(df_profit['profit_margin'], bins=bins, labels=labels)
        
        margin_dist = df_profit.groupby('margin_category', observed=True).agg({
            'BELEGNR': 'count',
            'BRUTTO': 'sum',
            'ERLOES': 'sum'
        }).reset_index()
        margin_dist.columns = ['Margin_Category', 'Order_Count', 'Total_Revenue', 'Total_Profit']
        results['margin_distribution'] = margin_dist
        
        # Profitability by platform
        if 'ORIGIN' in self.df.columns:
            platform_profit = df_profit.groupby('ORIGIN').agg({
                'BRUTTO': 'sum',
                'NETTO': 'sum',
                'ERLOES': 'sum',
                'profit_margin': 'mean'
            }).reset_index()
            platform_profit.columns = ['Platform', 'Gross_Revenue', 'Net_Revenue', 'Total_Profit', 'Avg_Margin']
            platform_profit['Profit_Margin_Pct'] = (platform_profit['Total_Profit'] / platform_profit['Gross_Revenue']) * 100
            results['platform_profitability'] = platform_profit
        
        # Profitability by country
        if 'ISOA2_LAND' in self.df.columns:
            country_profit = df_profit.groupby('ISOA2_LAND').agg({
                'BRUTTO': 'sum',
                'ERLOES': 'sum',
                'profit_margin': 'mean'
            }).reset_index()
            country_profit.columns = ['Country', 'Gross_Revenue', 'Total_Profit', 'Avg_Margin']
            country_profit['Profit_Margin_Pct'] = (country_profit['Total_Profit'] / country_profit['Gross_Revenue']) * 100
            country_profit = country_profit.sort_values('Total_Profit', ascending=False)
            results['country_profitability'] = country_profit
        
        # Top profitable orders
        top_orders = df_profit.nlargest(20, 'ERLOES')[['BELEGNR', 'ORDER_ID', 'NAME2', 'ORIGIN', 'BRUTTO', 'ERLOES', 'profit_margin']]
        top_orders.columns = ['Document_Nr', 'Order_ID', 'Customer', 'Platform', 'Gross_Revenue', 'Profit', 'Margin_%']
        results['top_profitable_orders'] = top_orders
        
        # Lowest margin orders (potentially problematic)
        low_margin = df_profit.nsmallest(20, 'profit_margin')[['BELEGNR', 'ORDER_ID', 'NAME2', 'ORIGIN', 'BRUTTO', 'ERLOES', 'profit_margin']]
        low_margin.columns = ['Document_Nr', 'Order_ID', 'Customer', 'Platform', 'Gross_Revenue', 'Profit', 'Margin_%']
        results['low_margin_orders'] = low_margin
        
        return results
    
    def get_payment_analysis(self) -> Dict[str, pd.DataFrame]:
        """Analyze by payment method."""
        results = {}
        
        if 'ZAHLART' not in self.df.columns:
            return results
        
        # Payment method breakdown
        payment_cols = {}
        if 'BRUTTO' in self.df.columns:
            payment_cols['BRUTTO'] = 'sum'
        if 'ERLOES' in self.df.columns:
            payment_cols['ERLOES'] = 'sum'
        
        if payment_cols:
            payment_cols['BELEGNR'] = 'count'
            payment_stats = self.df.groupby('ZAHLART').agg(payment_cols).reset_index()
            payment_stats.columns = ['Payment_Method', 'Total_Revenue', 'Total_Profit', 'Order_Count'] if 'ERLOES' in payment_cols else ['Payment_Method', 'Total_Revenue', 'Order_Count']
            payment_stats = payment_stats.sort_values('Total_Revenue', ascending=False)
            results['payment_summary'] = payment_stats
        
        return results
    
    def get_order_value_distribution(self) -> Dict[str, pd.DataFrame]:
        """Analyze order value distribution."""
        results = {}
        
        if 'BRUTTO' not in self.df.columns:
            return results
        
        # Order value histogram data
        df_orders = self.df[self.df['BRUTTO'] > 0].copy()
        
        # Define bins for order values
        max_val = df_orders['BRUTTO'].max()
        if max_val <= 100:
            bins = [0, 10, 20, 30, 50, 75, 100]
        elif max_val <= 500:
            bins = [0, 25, 50, 100, 150, 200, 300, 500]
        else:
            bins = [0, 50, 100, 200, 300, 500, 750, 1000, max_val + 1]
        
        labels = [f"€{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]
        df_orders['value_range'] = pd.cut(df_orders['BRUTTO'], bins=bins, labels=labels)
        
        value_dist = df_orders.groupby('value_range', observed=True).agg({
            'BRUTTO': ['count', 'sum']
        }).reset_index()
        value_dist.columns = ['Value_Range', 'Order_Count', 'Total_Revenue']
        results['order_value_distribution'] = value_dist
        
        # Statistics
        stats = {
            'mean': df_orders['BRUTTO'].mean(),
            'median': df_orders['BRUTTO'].median(),
            'std': df_orders['BRUTTO'].std(),
            'min': df_orders['BRUTTO'].min(),
            'max': df_orders['BRUTTO'].max(),
            'q25': df_orders['BRUTTO'].quantile(0.25),
            'q75': df_orders['BRUTTO'].quantile(0.75)
        }
        results['order_value_stats'] = pd.DataFrame([stats])
        
        return results
    
    def get_full_analysis(self) -> Dict[str, Any]:
        """Get complete analysis results."""
        return {
            'kpis': self.get_kpi_metrics(),
            'platform': self.get_platform_analysis(),
            'geographic': self.get_geographic_analysis(),
            'time': self.get_time_analysis(),
            'customer': self.get_customer_analysis(),
            'document_type': self.get_document_type_analysis(),
            'profitability': self.get_profitability_analysis(),
            'payment': self.get_payment_analysis(),
            'order_value': self.get_order_value_distribution()
        }


def analyze_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Convenience function to analyze a DataFrame."""
    analyzer = DataAnalyzer(df)
    return analyzer.get_full_analysis()