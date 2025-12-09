"""Configuration settings for Buchhaltung."""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DatabaseConfig:
    """Database configuration - supports SQLite (local) and PostgreSQL (production)."""
    # If DATABASE_URL is set (e.g., from Render PostgreSQL), use it
    # Otherwise, fall back to SQLite
    url: str = field(default_factory=lambda: os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).parent / 'instance' / 'buchhaltung.db'}"
    ))
    
    def __post_init__(self):
        # PostgreSQL URL fix for SQLAlchemy (Render uses postgres:// but SQLAlchemy needs postgresql://)
        if self.url.startswith("postgres://"):
            self.url = self.url.replace("postgres://", "postgresql://", 1)


@dataclass
class APIConfig:
    base_url: str = field(default_factory=lambda: os.environ.get("API_BASE_URL", "http://81.201.149.54:23100"))
    procedure_endpoint: str = field(default_factory=lambda: os.environ.get("API_PROCEDURE_ENDPOINT", "/procedures/IDM_APP_BELEGINFO"))
    connection_id: str = field(default_factory=lambda: os.environ.get("API_CONNECTION_ID", "c9a182ab-97bf-456e-a0eb-606bf97090d5"))
    timeout: int = field(default_factory=lambda: int(os.environ.get("API_TIMEOUT", "30")))
    
    @property
    def full_url(self) -> str:
        return f"{self.base_url}{self.procedure_endpoint}"
    
    @property
    def headers(self) -> dict:
        return {
            "Piper-Connection": self.connection_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }


@dataclass
class ExcelConfig:
    shop_data_header_row: int = 10
    api_order_column: str = "ORDER_ID"
    shop_order_column: str = "Bestellnummer"
    final_headers: List[str] = field(default_factory=lambda: [
        "Datum der Transaktionserstellung", "Typ", "Bestellnummer",
        "Alte Bestellnummer", "Nutzername des Kaeufers", "Name des Kaeufers",
        "KD-NR", "RG-NR", "Transaktionsbetrag (inkl. Kosten)",
        "Zwischensumme Artikel", "Fixer Anteil der Verkaufsprovision",
        "Variabler Anteil der Verkaufsprovision",
        "Gebuehr fuer sehr hohe Quote", "Gebuehr fuer unterdurchschnittlichen Servicestatus",
        "Internationale Gebuehr", "Betrag abzuegl. Kosten", "Auszahlung Nr.", "Auszahlungsdatum"
    ])


@dataclass
class AppConfig:
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    output_dir: Path = field(default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", str(Path(__file__).parent / "output"))))
    default_port: int = field(default_factory=lambda: int(os.environ.get("PORT", "7860")))
    port_range: tuple = (7860, 7880)
    share: bool = False
    debug: bool = field(default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true")
    theme: str = "soft"
    title: str = "Buchhaltung - Excel Processor"
    secret_key: str = field(default_factory=lambda: os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production"))
    
    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class Config:
    api: APIConfig = field(default_factory=APIConfig)
    excel: ExcelConfig = field(default_factory=ExcelConfig)
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)


config = Config()

def get_config() -> Config:
    return config

def get_output_path(filename: str) -> Path:
    return config.app.output_dir / filename
