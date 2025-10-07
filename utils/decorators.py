from functools import wraps
from flask import request, jsonify, g
import os

def require_token(f):
    """Require valid user token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        # Import here to avoid circular imports
        from models import User
        user = User.query.filter_by(token=token).first()
        
        if not user:
            return jsonify({'error': 'Invalid token'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """Require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key')
        
        if admin_key != os.getenv('ADMIN_SECRET_KEY'):
            return jsonify({'error': 'Unauthorized'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

