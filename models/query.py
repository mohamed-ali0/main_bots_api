from datetime import datetime
from models.base import db

class Query(db.Model):
    __tablename__ = 'queries'
    
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    platform = db.Column(db.String(50), default='emodal')
    status = db.Column(db.String(20), nullable=False, index=True)  # pending, in_progress, completed, failed
    folder_path = db.Column(db.String(500), nullable=False)
    summary_stats = db.Column(db.JSON, nullable=True)  # JSON field
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', back_populates='queries')
    
    # Create composite index
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f'<Query {self.query_id}>'

