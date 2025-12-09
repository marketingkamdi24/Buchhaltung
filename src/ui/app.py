"""
Modern Flask Web Application for Buchhaltung.
Professional interface for Excel processing workflow and data analytics.
"""
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import get_config, get_output_path
from src.api.client import APIClient
from src.processors.data_matcher import DataMatcher
from src.processors.data_analyzer import DataAnalyzer
from src.utils.helpers import find_available_port, is_port_in_use, kill_process_on_port


# Initialize Flask app
app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Store session data
api_data_store = {}  # session_id -> DataFrame

# Color palette for charts
COLORS = {
    'primary': '#4F46E5',
    'secondary': '#10B981',
    'accent': '#F59E0B',
    'danger': '#EF4444',
    'info': '#3B82F6',
    'success': '#22C55E',
    'warning': '#F97316',
    'purple': '#8B5CF6',
    'pink': '#EC4899',
    'teal': '#14B8A6'
}

PLATFORM_COLORS = {
    'Amazon': '#FF9900',
    'Ebay': '#E53238',
    'Kaufland': '#E31E24',
    'Unknown': '#9CA3AF'
}

COUNTRY_NAMES = {
    'DE': 'Germany',
    'AT': 'Austria',
    'FR': 'France',
    'CH': 'Switzerland',
    'IT': 'Italy',
    'ES': 'Spain',
    'NL': 'Netherlands',
    'BE': 'Belgium',
    'PL': 'Poland',
    'LU': 'Luxembourg',
    'Unknown': 'Unknown'
}


def get_session_id():
    """Get or create session ID."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_api_data():
    """Get API data from session store."""
    session_id = get_session_id()
    return api_data_store.get(session_id)


def set_api_data(df):
    """Store API data in session store."""
    session_id = get_session_id()
    api_data_store[session_id] = df


# Routes
@app.route('/')
def index():
    """Main dashboard with analytics."""
    return render_template('index.html', page='dashboard')


@app.route('/process')
def process_page():
    """Process Data page - unified fetch and process."""
    has_api_data = get_api_data() is not None
    return render_template('process.html', page='process', has_api_data=has_api_data)


@app.route('/help')
def help_page():
    """Help & Documentation page."""
    return render_template('help.html', page='help')


# API Endpoints
@app.route('/api/fetch-data', methods=['POST'])
def api_fetch_data():
    """API endpoint to fetch data from external API."""
    try:
        data = request.json
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        use_amazon = data.get('use_amazon', True)
        use_ebay = data.get('use_ebay', True)
        custom_origins = data.get('custom_origins', '')
        
        client = APIClient()
        response = client.fetch_data(date_from, date_to, use_amazon, use_ebay, custom_origins)
        
        if response.success and response.data is not None:
            set_api_data(response.data)
            
            # Store date range in session
            session['api_date_from'] = date_from
            session['api_date_to'] = date_to
            
            # Get download URL
            download_url = None
            if response.file_path:
                download_url = f'/api/download/{os.path.basename(response.file_path)}'
            
            # Prepare preview data
            preview_data = response.data.head(50).to_dict('records')
            columns = list(response.data.columns)
            
            return jsonify({
                'success': True,
                'message': response.message,
                'output_file': response.file_path,
                'download_url': download_url,
                'record_count': len(response.data),
                'column_count': len(response.data.columns),
                'preview': preview_data,
                'columns': columns
            })
        else:
            return jsonify({
                'success': False,
                'message': response.message
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@app.route('/api/process-data', methods=['POST'])
def api_process_data():
    """API endpoint to match and process shop data."""
    try:
        if 'shop_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['shop_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        api_data = get_api_data()
        if api_data is None:
            return jsonify({'success': False, 'message': 'Please fetch API data first (Step 1)'})
        
        # Save uploaded file temporarily
        config = get_config()
        filename = secure_filename(file.filename)
        temp_path = config.app.output_dir / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(str(temp_path))
        
        try:
            matcher = DataMatcher()
            result = matcher.match_and_process(api_data, str(temp_path))
            
            # Clean up temp file
            if temp_path.exists():
                os.remove(str(temp_path))
            
            if result.success:
                preview_data = result.data.head(50).to_dict('records') if result.data is not None else []
                columns = list(result.data.columns) if result.data is not None else []
                
                # Extract stats from result
                matched_count = getattr(result, 'matched_count', 0)
                unmatched_count = getattr(result, 'unmatched_count', 0)
                total_count = len(result.data) if result.data is not None else 0
                
                # Get download URLs
                matched_url = None
                modified_url = None
                if result.file_path:
                    matched_url = f'/api/download/{os.path.basename(result.file_path)}'
                if hasattr(result, 'modified_file_path') and result.modified_file_path:
                    modified_url = f'/api/download/{os.path.basename(result.modified_file_path)}'
                
                return jsonify({
                    'success': True,
                    'message': result.message,
                    'file_path': result.file_path,
                    'matched_count': matched_count,
                    'unmatched_count': unmatched_count,
                    'total_count': total_count,
                    'matched_url': matched_url,
                    'modified_url': modified_url,
                    'preview': preview_data,
                    'columns': columns
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result.message
                })
        except Exception as e:
            if temp_path.exists():
                os.remove(str(temp_path))
            raise e
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}\n{traceback.format_exc()}'
        })


@app.route('/api/analytics-data', methods=['POST'])
def api_analytics_data():
    """API endpoint to get analytics data."""
    try:
        data = request.json
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        use_amazon = data.get('use_amazon', True)
        use_ebay = data.get('use_ebay', True)
        custom_origins = data.get('custom_origins', '')
        
        client = APIClient()
        response = client.fetch_data(date_from, date_to, use_amazon, use_ebay, custom_origins)
        
        if not response.success or response.data is None:
            return jsonify({'success': False, 'message': response.message})
        
        analyzer = DataAnalyzer(response.data)
        
        # Generate all analytics
        kpis = analyzer.get_kpi_metrics()
        platform_data = analyzer.get_platform_analysis()
        geo_data = analyzer.get_geographic_analysis()
        time_data = analyzer.get_time_analysis()
        customer_data = analyzer.get_customer_analysis()
        profit_data = analyzer.get_profitability_analysis()
        payment_data = analyzer.get_payment_analysis()
        order_value_data = analyzer.get_order_value_distribution()
        
        # Create charts
        charts = {}
        
        # Platform revenue chart
        if 'platform_share' in platform_data:
            df = platform_data['platform_share']
            fig = px.pie(df, values='BRUTTO', names='ORIGIN', title='Revenue by Platform',
                        color='ORIGIN', color_discrete_map=PLATFORM_COLORS, hole=0.4)
            fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=350)
            charts['platform_revenue'] = json.loads(fig.to_json())
        
        # Platform orders chart
        if 'platform_orders' in platform_data:
            df = platform_data['platform_orders']
            fig = px.bar(df, x='ORIGIN', y='order_count', title='Orders by Platform',
                        color='ORIGIN', color_discrete_map=PLATFORM_COLORS, text='order_count')
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, margin=dict(t=40, b=40, l=60, r=20), height=350)
            charts['platform_orders'] = json.loads(fig.to_json())
        
        # Geographic chart
        if 'country_share' in geo_data:
            df = geo_data['country_share'].copy()
            df['Country_Name'] = df['ISOA2_LAND'].map(lambda x: COUNTRY_NAMES.get(x, x))
            fig = px.bar(df.head(10), x='Country_Name', y='BRUTTO', title='Revenue by Country (Top 10)',
                        color='BRUTTO', color_continuous_scale='Viridis')
            fig.update_layout(margin=dict(t=40, b=60, l=60, r=20), height=350, xaxis_tickangle=-45,
                            coloraxis_showscale=False)
            charts['geographic'] = json.loads(fig.to_json())
        
        # Daily trend chart
        if 'daily_trend' in time_data:
            df = time_data['daily_trend']
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            y_col = 'Gross_Revenue' if 'Gross_Revenue' in df.columns else df.columns[1]
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df[y_col], name='Revenue',
                line=dict(color=COLORS['primary'], width=2),
                fill='tozeroy', fillcolor='rgba(79, 70, 229, 0.1)'
            ), secondary_y=False)
            
            if 'Order_Count' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Date'], y=df['Order_Count'], name='Orders',
                    line=dict(color=COLORS['secondary'], width=2, dash='dot')
                ), secondary_y=True)
            
            fig.update_layout(title='Daily Revenue & Order Trend', height=350,
                            margin=dict(t=40, b=40, l=60, r=60), hovermode='x unified',
                            legend=dict(orientation="h", y=1.1))
            charts['daily_trend'] = json.loads(fig.to_json())
        
        # Day of week chart
        if 'day_of_week' in time_data:
            df = time_data['day_of_week']
            fig = px.bar(df, x='DayOfWeek', y='Total_Revenue', title='Revenue by Day of Week',
                        color='Total_Revenue', color_continuous_scale='Blues')
            fig.update_layout(margin=dict(t=40, b=40, l=60, r=20), height=350, coloraxis_showscale=False)
            charts['day_of_week'] = json.loads(fig.to_json())
        
        # Hourly chart
        if 'hourly_pattern' in time_data:
            df = time_data['hourly_pattern']
            fig = go.Figure(go.Bar(x=df['Hour'], y=df['Order_Count'], marker_color=COLORS['info']))
            fig.update_layout(title='Orders by Hour', margin=dict(t=40, b=40, l=60, r=20), height=350,
                            xaxis=dict(tickmode='linear', dtick=2))
            charts['hourly'] = json.loads(fig.to_json())
        
        # Customer frequency chart
        if 'customer_frequency' in customer_data:
            df = customer_data['customer_frequency']
            fig = px.pie(df, values='Customer_Count', names='Category',
                        title='Customer Distribution', hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=350)
            charts['customer_frequency'] = json.loads(fig.to_json())
        
        # Profit margin chart
        if 'margin_distribution' in profit_data:
            df = profit_data['margin_distribution']
            fig = px.bar(df, x='Margin_Category', y='Order_Count', title='Orders by Profit Margin',
                        color='Total_Profit', color_continuous_scale='RdYlGn')
            fig.update_layout(margin=dict(t=40, b=60, l=60, r=20), height=350, xaxis_tickangle=-45)
            charts['profit_margin'] = json.loads(fig.to_json())
        
        # Platform profitability chart
        if 'platform_profitability' in profit_data:
            df = profit_data['platform_profitability']
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['Platform'], y=df['Gross_Revenue'], name='Gross Revenue',
                                marker_color=COLORS['info']))
            fig.add_trace(go.Bar(x=df['Platform'], y=df['Total_Profit'], name='Profit',
                                marker_color=COLORS['success']))
            fig.update_layout(title='Platform Profitability', barmode='group', height=350,
                            margin=dict(t=40, b=40, l=60, r=20),
                            legend=dict(orientation="h", y=1.1))
            charts['platform_profitability'] = json.loads(fig.to_json())
        
        # Order value distribution chart
        if 'order_value_distribution' in order_value_data:
            df = order_value_data['order_value_distribution']
            fig = px.bar(df, x='Value_Range', y='Order_Count', title='Order Value Distribution',
                        color='Total_Revenue', color_continuous_scale='Purples')
            fig.update_layout(margin=dict(t=40, b=60, l=60, r=20), height=350, xaxis_tickangle=-45)
            charts['order_value'] = json.loads(fig.to_json())
        
        # Payment chart
        if 'payment_summary' in payment_data:
            df = payment_data['payment_summary']
            fig = px.pie(df, values='Total_Revenue', names='Payment_Method',
                        title='Revenue by Payment Method', hole=0.3,
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=350)
            charts['payment'] = json.loads(fig.to_json())
        
        # Prepare tables
        tables = {}
        if 'country_summary' in geo_data:
            df = geo_data['country_summary'].copy()
            df['Country'] = df['ISOA2_LAND'].map(lambda x: COUNTRY_NAMES.get(x, x))
            tables['countries'] = df[['Country', 'BRUTTO_sum', 'BRUTTO_count', 'BRUTTO_mean']].head(10).to_dict('records')
        
        if 'top_customers' in customer_data:
            tables['top_customers'] = customer_data['top_customers'].to_dict('records')
        
        return jsonify({
            'success': True,
            'kpis': kpis,
            'charts': charts,
            'tables': tables,
            'record_count': len(response.data)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}\n{traceback.format_exc()}'
        })


@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download a processed file."""
    try:
        config = get_config()
        file_path = config.app.output_dir / filename
        if file_path.exists():
            return send_file(str(file_path), as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-api-data')
def check_api_data():
    """Check if API data is available in session."""
    api_data = get_api_data()
    has_data = api_data is not None
    
    # Get stored date range info from session
    date_from = session.get('api_date_from', '')
    date_to = session.get('api_date_to', '')
    
    return jsonify({
        'has_data': has_data,
        'record_count': len(api_data) if has_data else 0,
        'date_from': date_from,
        'date_to': date_to
    })


def create_app():
    """Create and configure the Flask application."""
    return app


def main():
    """Main entry point for the application."""
    config = get_config()
    
    # Find available port
    port = config.app.default_port
    
    if is_port_in_use(port):
        print(f"Port {port} is in use. Attempting to find an alternative...")
        try:
            port = find_available_port(
                config.app.port_range[0],
                config.app.port_range[1]
            )
            print(f"Using port {port}")
        except RuntimeError:
            print(f"Attempting to kill process on port {config.app.default_port}...")
            success, msg = kill_process_on_port(config.app.default_port)
            print(msg)
            if success:
                port = config.app.default_port
            else:
                raise RuntimeError("Could not find or free a port for the application")
    
    print(f"\n{'='*60}")
    print(f"  Buchhaltung - Excel Processor & Analytics")
    print(f"{'='*60}")
    print(f"\n  Server running at: http://localhost:{port}")
    print(f"  Output directory: {config.app.output_dir}")
    print(f"\n  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.app.debug,
        threaded=True
    )


if __name__ == "__main__":
    main()