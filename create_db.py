"""Quick database setup script"""
from app import create_app
from models.base import db

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database created successfully!")

