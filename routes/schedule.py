from flask import Blueprint, request, jsonify, g
from utils.decorators import require_token
from models import db, User

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')

@schedule_bp.route('', methods=['GET'])
@require_token
def get_schedule():
    """
    Get user's schedule settings
    
    Response:
    {
        "success": true,
        "schedule": {
            "enabled": true,
            "frequency": 60
        }
    }
    """
    user = g.current_user
    
    return jsonify({
        'success': True,
        'schedule': {
            'enabled': user.schedule_enabled,
            'frequency': user.schedule_frequency
        }
    })


@schedule_bp.route('', methods=['PUT'])
@require_token
def update_schedule():
    """
    Update schedule settings
    
    Request:
    {
        "enabled": true,
        "frequency": 120
    }
    """
    user = g.current_user
    data = request.json
    
    if 'enabled' in data:
        user.schedule_enabled = data['enabled']
    
    if 'frequency' in data:
        frequency = int(data['frequency'])
        if frequency < 1:
            return jsonify({'error': 'Frequency must be at least 1 minute'}), 400
        user.schedule_frequency = frequency
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'schedule': {
            'enabled': user.schedule_enabled,
            'frequency': user.schedule_frequency
        }
    })


@schedule_bp.route('/pause', methods=['POST'])
@require_token
def pause_schedule():
    """Pause automated queries"""
    user = g.current_user
    user.schedule_enabled = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Schedule paused'})


@schedule_bp.route('/resume', methods=['POST'])
@require_token
def resume_schedule():
    """Resume automated queries"""
    user = g.current_user
    user.schedule_enabled = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Schedule resumed'})

