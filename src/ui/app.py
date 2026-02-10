"""
Modern Flask Web Application for Buchhaltung.
Professional interface for Excel processing workflow and data analytics.
"""
import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
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
from src.ui.models import db, User, init_db, upgrade_database


# Initialize Flask app
app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)

# Configure app
_config = get_config()
app.secret_key = _config.app.secret_key
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Session configuration - 15 minute timeout for security
SESSION_TIMEOUT_MINUTES = 15
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
# SESSION_COOKIE_SECURE should only be True in production with HTTPS
# Detect production by checking for render.com or FLASK_ENV
is_production = os.environ.get('FLASK_ENV') == 'production' or 'onrender.com' in os.environ.get('RENDER_EXTERNAL_URL', '')
app.config['SESSION_COOKIE_SECURE'] = is_production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request

# Database configuration
instance_path = Path(__file__).parent.parent.parent / 'instance'
instance_path.mkdir(parents=True, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{instance_path}/buchhaltung.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return db.session.get(User, int(user_id))


@app.before_request
def before_request():
    """
    Check session activity and expire if inactive for 15 minutes.
    This runs before every request to enforce session timeout.
    """
    # Skip for static files and login page
    if request.endpoint in ('static', 'login', 'robots_txt') or request.path.startswith('/static/'):
        return
    
    session.permanent = True
    now = datetime.utcnow()
    
    # Check if session has expired due to inactivity
    last_activity = session.get('last_activity')
    if last_activity:
        # Convert string back to datetime if needed
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity)
            except ValueError:
                last_activity = None
        
        if last_activity:
            inactive_time = now - last_activity
            if inactive_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                # Session has expired - clear everything
                session_id = session.get('session_id')
                if session_id and session_id in api_data_store:
                    del api_data_store[session_id]
                
                # Clear the session completely
                session.clear()
                
                # Force logout if user is authenticated
                if current_user.is_authenticated:
                    logout_user()
                
                # Redirect to login with message
                flash('Your session has expired due to inactivity. Please log in again.', 'warning')
                return redirect(url_for('login'))
    
    # Update last activity timestamp
    session['last_activity'] = now.isoformat()


@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access - return JSON for API requests, redirect for pages."""
    # Only return JSON for actual API endpoints (not regular pages)
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'message': 'Authentication required. Please log in.',
            'redirect': url_for('login')
        }), 401
    flash('Please log in to access this page.', 'info')
    return redirect(url_for('login', next=request.url))

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


# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Prevent search engine indexing
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy - restrict resource loading
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.plot.ly; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    
    # Strict Transport Security (only in production with HTTPS)
    if is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response


# Robots.txt route
@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt to disallow all crawlers."""
    content = """User-agent: *
Disallow: /
"""
    return content, 200, {'Content-Type': 'text/plain'}


# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication with security features."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        # Check if account is locked
        if user and user.is_locked():
            remaining_time = (user.locked_until - datetime.utcnow()).total_seconds() / 60
            flash(f'Account is locked due to too many failed attempts. Try again in {int(remaining_time) + 1} minutes.', 'error')
            return render_template('login.html')
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'error')
                return render_template('login.html')
            
            # Successful login - reset failed attempts
            login_user(user, remember=bool(remember))
            user.update_last_login()
            
            # Validate next URL to prevent open redirect vulnerability
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            # Record failed login attempt
            if user:
                user.record_failed_login()
                remaining_attempts = max(0, 5 - (user.failed_login_count or 0))
                if remaining_attempts > 0:
                    flash(f'Invalid username or password. {remaining_attempts} attempts remaining.', 'error')
                else:
                    flash('Account locked due to too many failed attempts. Please try again later.', 'error')
            else:
                # Don't reveal if username exists
                flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout the current user and clear all session data."""
    # Clear API data store for this session
    session_id = session.get('session_id')
    if session_id and session_id in api_data_store:
        del api_data_store[session_id]
    
    # Clear the session completely
    session.clear()
    
    # Logout user from Flask-Login
    logout_user()
    
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/api/session-status')
def session_status():
    """API endpoint to check session status for client-side timeout handling."""
    if not current_user.is_authenticated:
        return jsonify({
            'authenticated': False,
            'expired': True,
            'redirect': url_for('login')
        })
    
    last_activity = session.get('last_activity')
    now = datetime.utcnow()
    
    if last_activity:
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity)
            except ValueError:
                last_activity = now
        
        inactive_seconds = (now - last_activity).total_seconds()
        remaining_seconds = max(0, (SESSION_TIMEOUT_MINUTES * 60) - inactive_seconds)
    else:
        remaining_seconds = SESSION_TIMEOUT_MINUTES * 60
    
    return jsonify({
        'authenticated': True,
        'expired': False,
        'remaining_seconds': int(remaining_seconds),
        'timeout_minutes': SESSION_TIMEOUT_MINUTES
    })


@app.route('/')
@login_required
def index():
    """Main dashboard with analytics."""
    return render_template('index.html', page='dashboard')


@app.route('/process')
@login_required
def process_page():
    """Process Data page - unified fetch and process."""
    has_api_data = get_api_data() is not None
    return render_template('process.html', page='process', has_api_data=has_api_data)


@app.route('/amazon')
@login_required
def amazon_page():
    """Amazon Data Processing page."""
    return render_template('amazon.html', page='amazon')


@app.route('/help')
@login_required
def help_page():
    """Help & Documentation page."""
    return render_template('help.html', page='help')


# API Endpoints
@app.route('/api/fetch-data', methods=['POST'])
@login_required
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
            
            # Prepare preview data (replace NaN with None for valid JSON)
            preview_data = response.data.head(50).fillna(value=pd.NA).replace({pd.NA: None}).to_dict('records')
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
@login_required
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
                # Replace NaN with None for valid JSON serialization
                preview_data = result.data.head(50).fillna(value=pd.NA).replace({pd.NA: None}).to_dict('records') if result.data is not None else []
                columns = list(result.data.columns) if result.data is not None else []
                
                # Extract stats from result
                matched_count = getattr(result, 'matched_count', 0)
                unmatched_count = getattr(result, 'unmatched_count', 0)
                total_count = len(result.data) if result.data is not None else 0
                
                # Get download URLs
                matched_url = None
                modified_url = None
                if result.matched_file_path:
                    matched_url = f'/api/download/{os.path.basename(result.matched_file_path)}'
                if result.processed_file_path:
                    modified_url = f'/api/download/{os.path.basename(result.processed_file_path)}'
                
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
@login_required
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
@login_required
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
@login_required
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


# ============================================================================
# Amazon Processing API Endpoints
# ============================================================================

@app.route('/api/amazon/process-csv', methods=['POST'])
@login_required
def api_amazon_process_csv():
    """Process uploaded Amazon CSV file."""
    try:
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'message': 'Keine CSV-Datei hochgeladen'})
        
        file = request.files['csv_file']
        abrechnungsnummer = request.form.get('abrechnungsnummer', '').strip()
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Keine Datei ausgewählt'})
        
        if not abrechnungsnummer:
            return jsonify({'success': False, 'message': 'Abrechnungsnummer fehlt'})
        
        # Read CSV file, skip first 7 rows (row 8 is header)
        import io
        content = file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(content), sep=';', skiprows=7, decimal=',')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Filter by Abrechnungsnummer and Typ = Versanddienstleistungen
        filtered_df = df[
            (df['Abrechnungsnummer'].astype(str) == str(abrechnungsnummer)) &
            (df['Typ'] == 'Versanddienstleistungen')
        ].copy()
        
        if filtered_df.empty:
            return jsonify({
                'success': False, 
                'message': f'Keine Versanddienstleistungen für Abrechnungsnummer {abrechnungsnummer} gefunden'
            })
        
        # Calculate sum of Gesamt column
        filtered_df['Gesamt'] = pd.to_numeric(filtered_df['Gesamt'].astype(str).str.replace(',', '.'), errors='coerce')
        gesamt_sum = filtered_df['Gesamt'].sum()
        
        # Convert to records for JSON
        columns = list(filtered_df.columns)
        filtered_data = filtered_df.fillna('').to_dict('records')
        
        # Store in session for later use
        session['amazon_csv_data'] = filtered_data
        session['amazon_abrechnungsnummer'] = abrechnungsnummer
        
        return jsonify({
            'success': True,
            'message': 'CSV erfolgreich verarbeitet',
            'row_count': len(filtered_df),
            'gesamt_sum': gesamt_sum,
            'abrechnungsnummer': abrechnungsnummer,
            'columns': columns,
            'filtered_data': filtered_data,
            'all_data': filtered_data
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}\n{traceback.format_exc()}'
        })


@app.route('/api/amazon/fetch-api-data', methods=['POST'])
@login_required
def api_amazon_fetch_api_data():
    """Fetch API data for each Bestellnummer and stream progress."""
    import requests as req
    
    # Capture request data BEFORE entering the generator (to avoid context issues)
    data = request.json
    abrechnungsnummer = data.get('abrechnungsnummer', '')
    bestellnummern = data.get('bestellnummern', [])
    csv_data = session.get('amazon_csv_data', [])
    
    # Remove duplicates while preserving order
    unique_bestellnummern = list(dict.fromkeys(bestellnummern))
    
    def generate():
        try:
            yield f"data: {json.dumps({'type': 'init', 'total': len(unique_bestellnummern)})}\n\n"
            
            api_results = []
            api_errors = []  # Track API errors
            orders_no_data = []  # Track orders with no matching data
            
            # API configuration
            api_url = "http://81.201.149.54:23100/procedures/IDM_APP_Amazon"
            headers = {
                "Piper-Connection": "c9a182ab-97bf-456e-a0eb-606bf97090d5",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            for idx, order_id in enumerate(unique_bestellnummern):
                yield f"data: {json.dumps({'type': 'progress', 'current': idx + 1, 'order_id': order_id})}\n\n"
                
                try:
                    body = {
                        "Parameters": {
                            "iorder_id": str(order_id)
                        }
                    }
                    
                    response = req.get(api_url, headers=headers, json=body, timeout=30)
                    
                    if response.status_code == 200:
                        api_data = response.json()
                        
                        # Parse the response - look for entries
                        entries = []
                        if isinstance(api_data, dict):
                            if 'Entries' in api_data:
                                entries = api_data['Entries'] if isinstance(api_data['Entries'], list) else [api_data['Entries']]
                            elif 'data' in api_data:
                                entries = api_data['data'] if isinstance(api_data['data'], list) else [api_data['data']]
                            else:
                                entries = [api_data]
                        elif isinstance(api_data, list):
                            entries = api_data
                        
                        # Filter by TYP=Versanddienstleistun only (ABRECHNUNGSNR may differ)
                        found_match = False
                        for entry in entries:
                            if isinstance(entry, dict):
                                typ = str(entry.get('TYP', '')).strip()
                                
                                if typ == 'Versanddienstleistun':
                                    api_results.append(entry)
                                    found_match = True
                        
                        if not found_match:
                            # Count how many times this order appears in CSV
                            csv_count = len([r for r in csv_data if str(r.get('Bestellnummer', '')) == order_id])
                            orders_no_data.append({
                                'order_id': order_id,
                                'reason': 'Kein Eintrag mit TYP=Versanddienstleistun',
                                'entries_count': len(entries),
                                'csv_count': csv_count,
                                'api_entries': entries  # Include actual API entries for display
                            })
                    else:
                        api_errors.append({
                            'order_id': order_id,
                            'error': f'HTTP {response.status_code}'
                        })
                                    
                except Exception as e:
                    api_errors.append({
                        'order_id': order_id,
                        'error': str(e)
                    })
                    continue
            
            # Find ALL duplicates in CSV - any Bestellnummer that appears more than once
            # Group CSV rows by Bestellnummer
            duplicates = []
            csv_duplicates_list = []  # All duplicate CSV rows for display
            bestellnummer_counts_csv = {}
            for idx, row in enumerate(csv_data):
                bn = str(row.get('Bestellnummer', ''))
                row_with_index = dict(row)
                row_with_index['_csv_row_index'] = idx
                if bn in bestellnummer_counts_csv:
                    bestellnummer_counts_csv[bn].append(row_with_index)
                else:
                    bestellnummer_counts_csv[bn] = [row_with_index]
            
            # Identify all CSV duplicates (any row where Bestellnummer appears > 1 time)
            for bn, csv_rows in bestellnummer_counts_csv.items():
                if len(csv_rows) > 1:
                    for row in csv_rows:
                        csv_duplicates_list.append({
                            'bestellnummer': bn,
                            'count_in_csv': len(csv_rows),
                            'row': row
                        })
            
            # Group API rows by ORDER_ID
            bestellnummer_counts_api = {}
            for row in api_results:
                bn = str(row.get('ORDER_ID', row.get('BESTELLNUMMER', '')))
                if bn in bestellnummer_counts_api:
                    bestellnummer_counts_api[bn].append(row)
                else:
                    bestellnummer_counts_api[bn] = [row]
            
            # For each Bestellnummer: if CSV has more rows, duplicate the API row
            # to match CSV count, and track these as duplicates
            api_results_with_duplicates = list(api_results)  # Start with original results
            
            for bn, csv_rows in bestellnummer_counts_csv.items():
                api_rows = bestellnummer_counts_api.get(bn, [])
                csv_count = len(csv_rows)
                api_count = len(api_rows)
                
                if csv_count > api_count and api_rows:
                    # Need to duplicate the API row to match CSV count
                    duplicates_needed = csv_count - api_count
                    for i in range(duplicates_needed):
                        # Create a copy of the first API row and mark as duplicate
                        dup_row = dict(api_rows[0])
                        dup_row['_is_duplicate'] = True
                        api_results_with_duplicates.append(dup_row)
                        duplicates.append({
                            'bestellnummer': bn,
                            'csv_row': csv_rows[api_count + i],
                            'api_row': api_rows[0],
                            'reason': f'CSV hat {csv_count} Zeilen, API hat {api_count}'
                        })
            
            # Calculate API sum INCLUDING duplicated rows
            api_sum = sum(float(row.get('GESAMT', 0)) for row in api_results_with_duplicates)
            
            yield f"data: {json.dumps({'type': 'complete', 'api_data': api_results_with_duplicates, 'duplicates': duplicates, 'csv_duplicates': csv_duplicates_list, 'api_sum': api_sum, 'api_errors': api_errors, 'orders_no_data': orders_no_data, 'stats': {'total_orders': len(unique_bestellnummern), 'api_matches': len(api_results), 'api_with_dups': len(api_results_with_duplicates), 'errors': len(api_errors), 'no_data': len(orders_no_data), 'csv_duplicate_rows': len(csv_duplicates_list)}})}\n\n"
            
        except Exception as e:
            import traceback
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/api/amazon/download-results', methods=['POST'])
@login_required
def api_amazon_download_results():
    """Download Amazon comparison results as Excel."""
    try:
        data = request.json
        csv_data = data.get('csv_data', [])
        api_data = data.get('api_data', [])
        duplicates = data.get('duplicates', [])
        abrechnungsnummer = data.get('abrechnungsnummer', '')
        
        # Create Excel file with multiple sheets
        config = get_config()
        output_filename = f"amazon_vergleich_{abrechnungsnummer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = config.app.output_dir / output_filename
        
        with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
            # CSV Data sheet
            if csv_data:
                df_csv = pd.DataFrame(csv_data)
                # Add sum row
                if 'Gesamt' in df_csv.columns:
                    sum_row = {col: '' for col in df_csv.columns}
                    sum_row[df_csv.columns[0]] = 'SUMME'
                    sum_row['Gesamt'] = df_csv['Gesamt'].astype(float).sum()
                    df_csv = pd.concat([df_csv, pd.DataFrame([sum_row])], ignore_index=True)
                df_csv.to_excel(writer, sheet_name='CSV_Daten', index=False)
            
            # API Data sheet
            if api_data:
                df_api = pd.DataFrame(api_data)
                # Add sum row
                if 'GESAMT' in df_api.columns:
                    sum_row = {col: '' for col in df_api.columns}
                    sum_row[df_api.columns[0]] = 'SUMME'
                    sum_row['GESAMT'] = df_api['GESAMT'].astype(float).sum()
                    df_api = pd.concat([df_api, pd.DataFrame([sum_row])], ignore_index=True)
                df_api.to_excel(writer, sheet_name='API_Daten', index=False)
            
            # Duplicates sheet
            if duplicates:
                dup_rows = [d['csv_row'] for d in duplicates if d.get('csv_row')]
                if dup_rows:
                    df_dup = pd.DataFrame(dup_rows)
                    df_dup.to_excel(writer, sheet_name='Duplikate', index=False)
        
        return send_file(str(output_path), as_attachment=True, download_name=output_filename)
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}\n{traceback.format_exc()}'
        }), 500


def create_app():
    """Create and configure the Flask application."""
    # Run database migration to add new security columns if needed
    upgrade_database()
    
    # Database already initialized at module level with db.init_app(app)
    # Just ensure tables exist and create default user
    with app.app_context():
        db.create_all()
        from src.ui.models import create_default_user
        create_default_user()
    return app


def main():
    """Main entry point for the application."""
    config = get_config()
    
    # Run database migration to add new security columns if needed
    upgrade_database()
    
    # Ensure database tables exist and create default user
    with app.app_context():
        db.create_all()
        from src.ui.models import create_default_user
        create_default_user()
    
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