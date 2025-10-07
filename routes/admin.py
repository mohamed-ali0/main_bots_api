from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models import db, User
from utils.decorators import require_admin
from services.auth_service import generate_short_token
from services.file_service import FileService
import os
import json
import shutil

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users', methods=['POST'])
@require_admin
def create_user():
    """
    Create new user
    
    Request:
    {
        "name": "John Doe",
        "username": "jdoe",
        "password": "secure_password",
        "emodal_username": "jfernandez",
        "emodal_password": "taffie",
        "emodal_captcha_key": "7bf85bb6f37c9799543a2a463aab2b4f"
    }
    """
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Generate token
    token = generate_short_token()
    
    # Create user folder (temporary path)
    user_id = User.query.count() + 1  # Temporary, will be replaced with actual ID
    folder_path = os.path.join('storage', 'users', str(user_id))
    
    # Create user
    user = User(
        name=data['name'],
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        token=token,
        folder_path=folder_path
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Update folder path with actual ID
    user.folder_path = os.path.join('storage', 'users', str(user.id))
    db.session.commit()
    
    # Create folder structure
    FileService.create_user_folders(user)
    
    # Create user_cre_env.json
    FileService.create_user_credentials(user, data)
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'username': user.username,
            'token': user.token,
            'folder_path': user.folder_path
        }
    }), 201


@admin_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    """List all users"""
    users = User.query.all()
    return jsonify({
        'success': True,
        'users': [{
            'id': u.id,
            'name': u.name,
            'username': u.username,
            'schedule_enabled': u.schedule_enabled,
            'query_count': len(u.queries),
            'created_at': u.created_at.isoformat()
        } for u in users]
    })


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user(user_id):
    """Get user details"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'username': user.username,
            'token': user.token,
            'folder_path': user.folder_path,
            'session_id': user.session_id,
            'schedule_enabled': user.schedule_enabled,
            'schedule_frequency': user.schedule_frequency,
            'query_count': len(user.queries),
            'created_at': user.created_at.isoformat()
        }
    })


@admin_bp.route('/users/<int:user_id>/credentials', methods=['PUT'])
@require_admin
def update_credentials(user_id):
    """
    Update user platform credentials
    
    Request:
    {
        "platform": "emodal",
        "credentials": {
            "username": "new_user",
            "password": "new_pass",
            "captcha_api_key": "new_key"
        }
    }
    """
    user = User.query.get_or_404(user_id)
    data = request.json
    
    # Load existing credentials
    creds_file = os.path.join(user.folder_path, 'user_cre_env.json')
    with open(creds_file, 'r') as f:
        creds = json.load(f)
    
    # Update platform credentials
    platform = data['platform']
    creds[platform] = data['credentials']
    
    # Save back
    with open(creds_file, 'w') as f:
        json.dump(creds, f, indent=2)
    
    # Invalidate session if emodal credentials changed
    if platform == 'emodal':
        user.session_id = None
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Credentials updated'})


@admin_bp.route('/users/<int:user_id>/flush', methods=['DELETE'])
@require_admin
def flush_user(user_id):
    """Delete user and all their data"""
    user = User.query.get_or_404(user_id)
    
    # Delete folder
    if os.path.exists(user.folder_path):
        shutil.rmtree(user.folder_path)
    
    # Delete from database (cascade will delete queries)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User and all data deleted'})

