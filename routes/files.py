from flask import Blueprint, request, jsonify, g, send_file
from utils.decorators import require_token
from models.query import Query
import os

files_bp = Blueprint('files', __name__, url_prefix='/files')

@files_bp.route('/containers/update', methods=['POST'])
@require_token
def update_containers():
    """
    Manually update all_containers.xlsx file
    
    Request (optional):
    {
        "force_new_session": false
    }
    
    Response:
    {
        "success": true,
        "message": "Containers file updated",
        "containers_count": 156,
        "file_path": "storage/users/1/emodal/all_containers.xlsx"
    }
    """
    user = g.current_user
    
    try:
        from flask import current_app
        from services.file_service import FileService
        from models import db
        
        emodal_client = current_app.config.get('EMODAL_CLIENT')
        
        # Check if we should force new session
        data = request.get_json() or {}
        force_new_session = data.get('force_new_session', False)
        
        # Ensure user has active session
        if not user.session_id or force_new_session:
            # Load credentials and create new session
            creds = FileService.load_user_credentials(user)
            emodal_creds = creds.get('emodal', {})
            
            if not emodal_creds.get('username') or not emodal_creds.get('password'):
                return jsonify({'error': 'E-Modal credentials not configured'}), 400
            
            session_response = emodal_client.get_session(
                username=emodal_creds['username'],
                password=emodal_creds['password'],
                captcha_api_key=emodal_creds.get('captcha_api_key', '')
            )
            
            if not session_response.get('success'):
                return jsonify({
                    'error': 'Failed to create E-Modal session',
                    'details': session_response.get('error', 'Unknown error')
                }), 500
            
            user.session_id = session_response['session_id']
            db.session.commit()
        
        # Get containers
        try:
            containers_response = emodal_client.get_containers(user.session_id)
        except Exception as e:
            # If failed, try with new session
            error_msg = str(e)
            if '400' in error_msg or 'BAD REQUEST' in error_msg:
                # Session likely invalid, create new one
                creds = FileService.load_user_credentials(user)
                emodal_creds = creds.get('emodal', {})
                
                session_response = emodal_client.get_session(
                    username=emodal_creds['username'],
                    password=emodal_creds['password'],
                    captcha_api_key=emodal_creds.get('captcha_api_key', '')
                )
                
                if not session_response.get('success'):
                    return jsonify({'error': 'Failed to create new E-Modal session', 'details': str(e)}), 500
                
                user.session_id = session_response['session_id']
                db.session.commit()
                
                # Retry with new session
                containers_response = emodal_client.get_containers(user.session_id)
            else:
                raise
        
        if not containers_response.get('success'):
            return jsonify({
                'error': 'Failed to get containers',
                'details': containers_response.get('error', 'Unknown error')
            }), 500
        
        # Download and save file
        import os
        master_containers = os.path.join(user.folder_path, 'emodal', 'all_containers.xlsx')
        os.makedirs(os.path.dirname(master_containers), exist_ok=True)
        emodal_client.download_file(containers_response['file_url'], master_containers)
        
        return jsonify({
            'success': True,
            'message': 'Containers file updated',
            'containers_count': containers_response.get('containers_count', 0),
            'file_path': master_containers
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/appointments/update', methods=['POST'])
@require_token
def update_appointments():
    """
    Manually update all_appointments.xlsx file
    
    Request (optional):
    {
        "force_new_session": false
    }
    
    Response:
    {
        "success": true,
        "message": "Appointments file updated",
        "appointments_count": 12,
        "file_path": "storage/users/1/emodal/all_appointments.xlsx"
    }
    """
    user = g.current_user
    
    try:
        from flask import current_app
        from services.file_service import FileService
        from models import db
        
        emodal_client = current_app.config.get('EMODAL_CLIENT')
        
        # Check if we should force new session
        data = request.get_json() or {}
        force_new_session = data.get('force_new_session', False)
        
        # Ensure user has active session
        if not user.session_id or force_new_session:
            # Load credentials and create new session
            creds = FileService.load_user_credentials(user)
            emodal_creds = creds.get('emodal', {})
            
            if not emodal_creds.get('username') or not emodal_creds.get('password'):
                return jsonify({'error': 'E-Modal credentials not configured'}), 400
            
            session_response = emodal_client.get_session(
                username=emodal_creds['username'],
                password=emodal_creds['password'],
                captcha_api_key=emodal_creds.get('captcha_api_key', '')
            )
            
            if not session_response.get('success'):
                return jsonify({
                    'error': 'Failed to create E-Modal session',
                    'details': session_response.get('error', 'Unknown error')
                }), 500
            
            user.session_id = session_response['session_id']
            db.session.commit()
        
        # Get appointments
        try:
            appointments_response = emodal_client.get_appointments(user.session_id)
        except Exception as e:
            # If failed, try with new session
            error_msg = str(e)
            if '400' in error_msg or 'BAD REQUEST' in error_msg:
                # Session likely invalid, create new one
                creds = FileService.load_user_credentials(user)
                emodal_creds = creds.get('emodal', {})
                
                session_response = emodal_client.get_session(
                    username=emodal_creds['username'],
                    password=emodal_creds['password'],
                    captcha_api_key=emodal_creds.get('captcha_api_key', '')
                )
                
                if not session_response.get('success'):
                    return jsonify({'error': 'Failed to create new E-Modal session', 'details': str(e)}), 500
                
                user.session_id = session_response['session_id']
                db.session.commit()
                
                # Retry with new session
                appointments_response = emodal_client.get_appointments(user.session_id)
            else:
                raise
        
        if not appointments_response.get('success'):
            return jsonify({
                'error': 'Failed to get appointments',
                'details': appointments_response.get('error', 'Unknown error')
            }), 500
        
        # Download and save file
        import os
        master_appointments = os.path.join(user.folder_path, 'emodal', 'all_appointments.xlsx')
        os.makedirs(os.path.dirname(master_appointments), exist_ok=True)
        emodal_client.download_file(appointments_response['file_url'], master_appointments)
        
        return jsonify({
            'success': True,
            'message': 'Appointments file updated',
            'appointments_count': appointments_response.get('selected_count', 0),
            'file_path': master_appointments
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/containers', methods=['GET'])
@require_token
def get_latest_containers():
    """Get latest all_containers.xlsx"""
    user = g.current_user
    file_path = os.path.join(user.folder_path, 'emodal', 'all_containers.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='all_containers.xlsx'
    )


@files_bp.route('/appointments', methods=['GET'])
@require_token
def get_latest_appointments():
    """Get latest all_appointments.xlsx"""
    user = g.current_user
    file_path = os.path.join(user.folder_path, 'emodal', 'all_appointments.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='all_appointments.xlsx'
    )


@files_bp.route('/queries/<query_id>/all-containers', methods=['GET'])
@require_token
def get_query_all_containers(query_id):
    """Get all_containers.xlsx for specific query"""
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    file_path = os.path.join(query.folder_path, 'all_containers.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{query_id}_all_containers.xlsx'
    )


@files_bp.route('/queries/<query_id>/filtered-containers', methods=['GET'])
@require_token
def get_query_filtered_containers(query_id):
    """Get filtered_containers.xlsx for specific query"""
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    file_path = os.path.join(query.folder_path, 'filtered_containers.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{query_id}_filtered_containers.xlsx'
    )


@files_bp.route('/queries/<query_id>/all-appointments', methods=['GET'])
@require_token
def get_query_all_appointments(query_id):
    """Get all_appointments.xlsx for specific query"""
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    file_path = os.path.join(query.folder_path, 'all_appointments.xlsx')
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{query_id}_all_appointments.xlsx'
    )


@files_bp.route('/queries/<query_id>/responses/<filename>', methods=['GET'])
@require_token
def get_response_file(query_id, filename):
    """Get specific response JSON file"""
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    file_path = os.path.join(
        query.folder_path,
        'containers_checking_attempts',
        'responses',
        filename
    )
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )


@files_bp.route('/queries/<query_id>/screenshots/<filename>', methods=['GET'])
@require_token
def get_screenshot_file(query_id, filename):
    """Get specific screenshot file"""
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    file_path = os.path.join(
        query.folder_path,
        'containers_checking_attempts',
        'screenshots',
        filename
    )
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='image/png',
        as_attachment=False
    )

