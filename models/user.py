from datetime import datetime
from models.base import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(50), unique=True, nullable=False, index=True)
    folder_path = db.Column(db.String(500), nullable=False)
    session_id = db.Column(db.String(255), nullable=True)  # E-Modal session
    schedule_enabled = db.Column(db.Boolean, default=True)
    schedule_frequency = db.Column(db.Integer, default=60)  # minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    queries = db.relationship('Query', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

