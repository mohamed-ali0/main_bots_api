import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///emodal.db'  # Using SQLite for easy setup
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Internal E-Modal API
    EMODAL_API_URL = os.getenv('EMODAL_API_URL', 'http://localhost:5010')
    
    # Admin
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'your-admin-key-here')
    
    # Storage
    STORAGE_PATH = os.getenv('STORAGE_PATH', 'storage')
    
    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'UTC'

