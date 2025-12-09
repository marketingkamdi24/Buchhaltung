# Buchhaltung - Professional Excel Processing Tool

A modern web-based Excel processing application with API integration for accounting workflows. Built with Python and Flask for a professional, responsive user interface.

## 🚀 Quick Start

### Windows

**Setup (one command):**
```batch
setup.bat
```

**Run (one command):**
```batch
start.bat
```

### Linux/Mac

**Setup (one command):**
```bash
chmod +x setup.sh && ./setup.sh
```

**Run (one command):**
```bash
chmod +x start.sh && ./start.sh
```

Then open your browser and navigate to: **http://localhost:7860**

**Default Login Credentials:**
- Username: `buchhaltung`
- Password: `buchhaltung123`

## ✨ Features

- **Professional Web UI**: Modern, responsive interface built with Flask and Bootstrap 5
- **User Authentication**: Secure login system with password hashing
- **Dark/Light Theme**: Toggle between themes for comfortable viewing
- **Two-Step Workflow**: Fetch API data → Match & Process shop data
- **Comprehensive Analytics**: Interactive charts and KPI dashboards
- **Excel Processing**: 20+ automated transformation operations
- **Data Matching**: Smart ORDER_ID to Bestellnummer matching
- **Multi-Platform Support**: Amazon, eBay, and custom platform support

## 📋 Screenshots

### Dashboard
Clean, modern dashboard with workflow overview and quick access to all features.

### Data Analytics
Interactive charts powered by Plotly for comprehensive sales analysis:
- Revenue by platform and country
- Time-based trends (daily, weekly, hourly)
- Customer analysis and profitability insights

## 🛠️ Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Manual Installation

1. Clone or download the project:
```bash
cd Buchhaltung-2
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the application:
```bash
python run.py
```

## 📖 Workflow Guide

### Step 1: Fetch API Data 🌐

1. Navigate to **Step 1: Fetch Data** in the sidebar
2. Enter date range in **DD.MM.YYYY** format
3. Select platforms (Amazon, eBay) or add custom origins
4. Click **"Fetch Data from API"**
5. Preview the data with ORDER_ID, KUNDENNR, and BELEGNR columns
6. Download the fetched data (optional)

### Step 2: Match & Process Shop Data 📊

1. Navigate to **Step 2: Process** in the sidebar
2. Ensure Step 1 is completed (green indicator shows API data is loaded)
3. Upload your eBay shop export Excel file
4. File must have **Bestellnummer** column in row 11
5. Click **"Match & Process Data"**
6. Download the processed file

### Data Analytics 📈

1. Navigate to **Data Analytics** in the sidebar
2. Configure date range and platforms
3. Click **"Load & Analyze"**
4. Explore interactive charts and insights:
   - Key Performance Indicators (KPIs)
   - Platform comparison
   - Geographic analysis
   - Time-based trends
   - Customer insights
   - Profitability analysis

## 🔧 Excel Transformation Rules

The following operations are applied automatically:

| # | Rule Description |
|---|------------------|
| 1 | Header extraction (Verkäufer, Betrag, Transaktionen) |
| 2 | Data matching (Bestellnummer ↔ ORDER_ID) |
| 3 | Row restructuring (data from row 5, headers in row 4) |
| 4 | Column organization (standard A-R format) |
| 5 | KD-NR / RG-NR mapping from API data |
| 6 | Verification columns (T: copy of J, U: =J-T formula) |
| 7 | Andere Gebühr handling (moved to Sheet 2) |
| 8 | Fee aggregation (Gebuehr row with SUM formulas) |
| 9 | Value conversion (-- → 0) |
| 10 | Verpackung und Versand addition |

### Output Format

**Main Sheet Structure (Columns A-R):**
- Row 1: Verkäufer | [seller name]
- Row 2: Transaktionen | [count]
- Row 3: Betrag | [total amount]
- Row 4: Column Headers
- Row 5+: Transaction Data
- Gebuehr Row: Sum of all fees
- Andere Gebuehr Row: Sum of "Andere Gebühr"
- Totals Row: SUM formulas

**Column Definitions:**
| Column | Header |
|--------|--------|
| A | Datum der Transaktionserstellung |
| B | Typ |
| C | Bestellnummer |
| D | Alte Bestellnummer |
| E | Nutzername des Käufers |
| F | Name des Käufers |
| G | KD-NR (from KUNDENNR) |
| H | RG-NR (from BELEGNR) |
| I | Transaktionsbetrag (inkl. Kosten) |
| J | Zwischensumme Artikel |
| K | Fixer Anteil der Verkaufsprovision |
| L | Variabler Anteil der Verkaufsprovision |
| M | Gebühr für hohe Quote |
| N | Gebühr für Servicestatus |
| O | Internationale Gebühr |
| P | Betrag abzügl. Kosten |
| Q | Auszahlung Nr. |
| R | Auszahlungsdatum |

## 📁 Project Structure

```
Buchhaltung-2/
├── config.py                 # Application configuration
├── run.py                    # Main entry point
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project metadata
├── setup.bat                # Windows setup script
├── setup.sh                 # Unix setup script
├── start.bat                # Windows start script
├── start.sh                 # Unix start script
├── README.md                # This file
├── output/                  # Generated files directory
└── src/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   └── client.py        # API client for data fetching
    ├── processors/
    │   ├── __init__.py
    │   ├── data_analyzer.py # Data analysis module
    │   ├── data_matcher.py  # Shop data matching
    │   └── excel_processor.py # Excel transformations
    ├── ui/
    │   ├── __init__.py
    │   ├── app.py           # Flask application
    │   ├── templates/       # HTML templates
    │   │   ├── base.html
    │   │   ├── index.html
    │   │   ├── fetch_data.html
    │   │   ├── process_data.html
    │   │   ├── analytics.html
    │   │   └── help.html
    │   └── static/          # Static assets
    │       ├── css/
    │       │   └── style.css
    │       └── js/
    │           └── main.js
    └── utils/
        ├── __init__.py
        └── helpers.py       # Utility functions
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **API Settings**: URL, connection ID, timeout
- **Excel Settings**: Header row, column mappings
- **App Settings**: Port, theme, debug mode

### Default Port

The application runs on port **7860** by default. If the port is in use, it will:
1. Try to find an available port in range 7860-7880
2. If no port is available, attempt to kill the process using port 7860

## 🌐 API Information

- **Endpoint**: `http://81.201.149.54:23100/procedures/IDM_APP_BELEGINFO`
- **Method**: GET with JSON body
- **Connection ID**: c9a182ab-97bf-456e-a0eb-606bf97090d5

### Request Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| IDATE_FROM | Start date | "28.10.2025" |
| IDATE_TO | End date | "29.10.2025" |
| IORIGIN | Origin filter | "'Amazon','Ebay'" |

### Required API Columns

| Column | Purpose |
|--------|---------|
| ORDER_ID | Matching key (↔ Bestellnummer) |
| KUNDENNR | Maps to KD-NR column |
| BELEGNR | Maps to RG-NR column |

## 🐛 Troubleshooting

### Port Already in Use

The application automatically handles port conflicts. If issues persist:

```bash
# Windows - find and kill process
netstat -ano | findstr :7860
taskkill /F /PID <PID>

# Linux/Mac
lsof -ti :7860 | xargs kill -9
```

### Virtual Environment Issues

```bash
# Remove and recreate
rm -rf venv
python -m venv venv
```

### Import Errors

Ensure you're running from the project root directory:
```bash
cd Buchhaltung-2
python run.py
```

### No API Data Error

Make sure to complete Step 1 before Step 2:
1. Go to Step 1: Fetch Data
2. Enter valid date range
3. Click Fetch Data
4. Wait for success message
5. Then proceed to Step 2

## 💡 Tips

- Use the theme toggle (moon/sun icon) for dark mode
- All output files are saved in the `output` folder with timestamps
- The sidebar can be collapsed on mobile devices
- Check processing logs for detailed status of each operation

## 🔐 Authentication

The application requires authentication. A default user is created automatically on first run:

- **Username**: `buchhaltung`
- **Password**: `buchhaltung123`

All routes are protected and require login. After authentication, you can:
- Access the dashboard and all features
- Your session is maintained across browser sessions (if "Remember me" is checked)
- Logout via the sidebar button

## 🚀 Deployment on Render

### Automatic Deployment (Recommended)

The project includes a `render.yaml` blueprint that configures everything automatically:

1. Push your code to GitHub
2. Connect your GitHub repository to Render
3. Create a new **Blueprint** deployment
4. Render will automatically:
   - Create a PostgreSQL database
   - Set up the web service
   - Configure all environment variables

### Manual Deployment

1. Create a new **Web Service** on Render
2. Create a new **PostgreSQL** database
3. Set the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection URL (auto-set if using Render PostgreSQL) | Yes |
| `SECRET_KEY` | Flask secret key (generate a secure random string) | Yes |
| `DEBUG` | Set to "false" for production | Yes |
| `API_BASE_URL` | External API base URL | Yes |
| `API_CONNECTION_ID` | API connection identifier | Yes |
| `API_PROCEDURE_ENDPOINT` | API procedure endpoint | Optional |
| `API_TIMEOUT` | API request timeout in seconds | Optional |

### Environment Variables for Login

The login system uses the following configuration:

- **`SECRET_KEY`**: Used for session encryption. Render auto-generates this.
- **`DATABASE_URL`**: The PostgreSQL connection string. The app automatically handles the `postgres://` vs `postgresql://` difference.

**No additional environment variables are needed for the login functionality** - the default user is created automatically when the database is initialized.

## 📄 License

MIT License - Feel free to use and modify.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Buchhaltung v2.2.0** | Professional Excel Processing Tool with API Integration and User Authentication