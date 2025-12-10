"""
Database models for Buchhaltung application.
User management with SQLAlchemy.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
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


def create_default_user():
    """Create the default admin user if it doesn't exist."""
    default_username = 'buchhaltung'
    default_password = 'buchhaltung123'
    
    existing_user = User.query.filter_by(username=default_username).first()
    if not existing_user:
        user = User(username=default_username)
        user.set_password(default_password)
        db.session.add(user)
        db.session.commit()
        print(f"Default user '{default_username}' created successfully.")
    else:
        print(f"Default user '{default_username}' already exists.")