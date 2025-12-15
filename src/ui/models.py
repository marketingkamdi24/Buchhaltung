"""
Database models for Buchhaltung application.
User management with SQLAlchemy.
"""
import os
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Security configuration from environment variables
# Credentials are set via APP_USERNAME and APP_PASSWORD environment variables
DEFAULT_USERNAME = os.environ.get('APP_USERNAME', 'buchhaltung')
DEFAULT_PASSWORD = os.environ.get('APP_PASSWORD', 'buchhaltung123')

# Failed login tracking (in-memory, resets on restart)
_failed_login_attempts = {}  # username -> {'count': int, 'locked_until': datetime}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """Hash and set the user's password using strong hashing."""
        # Using pbkdf2:sha256 with high iterations for security
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:600000'  # 600,000 iterations for strong security
        )
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if the account is currently locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def record_failed_login(self):
        """Record a failed login attempt and lock if necessary."""
        self.failed_login_count = (self.failed_login_count or 0) + 1
        if self.failed_login_count >= MAX_FAILED_ATTEMPTS:
            self.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        db.session.commit()
    
    def reset_failed_logins(self):
        """Reset failed login counter after successful login."""
        self.failed_login_count = 0
        self.locked_until = None
        db.session.commit()
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        self.reset_failed_logins()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Create default user if not exists
        create_default_user()


def upgrade_database():
    """Upgrade existing database schema to add new security columns.
    
    This handles the case where the database already exists with old schema.
    """
    import sqlite3
    from pathlib import Path
    
    instance_path = Path(__file__).parent.parent.parent / 'instance'
    db_path = instance_path / 'buchhaltung.db'
    
    if not db_path.exists():
        return  # New database, will be created fresh
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if new columns exist and add them if not
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'failed_login_count' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_count INTEGER DEFAULT 0")
            print("Added failed_login_count column to users table")
        
        if 'locked_until' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until DATETIME")
            print("Added locked_until column to users table")
        
        conn.commit()
    except Exception as e:
        print(f"Database upgrade error (may be expected): {e}")
    finally:
        conn.close()


def create_default_user():
    """Create the default user if it doesn't exist, or update password if it changed.
    
    Credentials are configured via APP_USERNAME and APP_PASSWORD environment variables.
    """
    username = DEFAULT_USERNAME
    password = DEFAULT_PASSWORD
    
    existing_user = User.query.filter_by(username=username).first()
    if not existing_user:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"User '{username}' created successfully.")
    else:
        # Always update the password to ensure it uses the latest hashing and value
        existing_user.set_password(password)
        existing_user.failed_login_count = 0  # Reset any lockout
        existing_user.locked_until = None
        db.session.commit()
        print(f"User '{username}' password updated.")