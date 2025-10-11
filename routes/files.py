from flask import Blueprint, request, jsonify, g, send_file
from utils.decorators import require_token
from models.query import Query
import os
import zipfile
import tempfile
import json
from datetime import datetime, timedelta

files_bp = Blueprint('files', __name__, url_prefix='/files')

@files_bp.route('/containers/update', methods=['POST'])
@require_token
def update_containers():
    """
    Manually update all_containers.xlsx file
    
    Request (optional):
    {
        "platform": "emodal",  // default: "emodal"
        "force_new_session": false
    }
    
    Response:
    {
        "success": true,
        "platform": "emodal",
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
        
        # Get platform from request (default: emodal)
        data = request.get_json() or {}
        platform = data.get('platform', 'emodal')
        force_new_session = data.get('force_new_session', False)
        
        # Get client based on platform
        if platform == 'emodal':
            client = current_app.config.get('EMODAL_CLIENT')
        else:
            return jsonify({'error': f'Unsupported platform: {platform}'}), 400
        
        emodal_client = client  # Keep backward compatibility
        
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
            'platform': platform,
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
        "platform": "emodal",  // default: "emodal"
        "force_new_session": false
    }
    
    Response:
    {
        "success": true,
        "platform": "emodal",
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
        
        # Get platform from request (default: emodal)
        data = request.get_json() or {}
        platform = data.get('platform', 'emodal')
        force_new_session = data.get('force_new_session', False)
        
        # Get client based on platform
        if platform == 'emodal':
            client = current_app.config.get('EMODAL_CLIENT')
        else:
            return jsonify({'error': f'Unsupported platform: {platform}'}), 400
        
        emodal_client = client  # Keep backward compatibility
        
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
            'platform': platform,
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


@files_bp.route('/containers/<container_number>/screenshots', methods=['GET'])
@require_token
def get_container_screenshots(container_number):
    """
    Get all screenshots for a specific container across all queries
    
    Returns a zip file containing all screenshots for the container
    
    Response:
    - ZIP file with format: {container_number}_screenshots_{timestamp}.zip
    - Contains all screenshots found across all user's queries
    """
    user = g.current_user
    
    try:
        # Get all queries for this user
        queries = Query.query.filter_by(user_id=user.id).all()
        
        if not queries:
            return jsonify({'error': 'No queries found'}), 404
        
        # Collect all screenshot files matching the container number
        screenshot_files = []
        
        for query in queries:
            screenshots_dir = os.path.join(
                query.folder_path,
                'containers_checking_attempts',
                'screenshots'
            )
            
            if os.path.exists(screenshots_dir):
                # Find all files that start with the container number
                for filename in os.listdir(screenshots_dir):
                    if filename.startswith(container_number):
                        file_path = os.path.join(screenshots_dir, filename)
                        if os.path.isfile(file_path):
                            screenshot_files.append({
                                'path': file_path,
                                'name': f"{query.query_id}_{filename}",
                                'query_id': query.query_id
                            })
        
        if not screenshot_files:
            return jsonify({
                'error': f'No screenshots found for container {container_number}'
            }), 404
        
        # Create a temporary zip file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"{container_number}_screenshots_{timestamp}.zip"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            zip_path = tmp_file.name
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in screenshot_files:
                    # Add file to zip with query_id prefix
                    zipf.write(file_info['path'], file_info['name'])
        
        # Send the zip file and delete it after sending
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/containers/<container_number>/responses', methods=['GET'])
@require_token
def get_container_responses(container_number):
    """
    Get all response files for a specific container across all queries
    
    Returns a zip file containing all response JSON files for the container
    
    Response:
    - ZIP file with format: {container_number}_responses_{timestamp}.zip
    - Contains all response JSON files found across all user's queries
    """
    user = g.current_user
    
    try:
        # Get all queries for this user
        queries = Query.query.filter_by(user_id=user.id).all()
        
        if not queries:
            return jsonify({'error': 'No queries found'}), 404
        
        # Collect all response files matching the container number
        response_files = []
        
        for query in queries:
            responses_dir = os.path.join(
                query.folder_path,
                'containers_checking_attempts',
                'responses'
            )
            
            if os.path.exists(responses_dir):
                # Find all files that start with the container number
                for filename in os.listdir(responses_dir):
                    if filename.startswith(container_number):
                        file_path = os.path.join(responses_dir, filename)
                        if os.path.isfile(file_path):
                            response_files.append({
                                'path': file_path,
                                'name': f"{query.query_id}_{filename}",
                                'query_id': query.query_id
                            })
        
        if not response_files:
            return jsonify({
                'error': f'No response files found for container {container_number}'
            }), 404
        
        # Create a temporary zip file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"{container_number}_responses_{timestamp}.zip"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            zip_path = tmp_file.name
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in response_files:
                    # Add file to zip with query_id prefix
                    zipf.write(file_info['path'], file_info['name'])
        
        # Send the zip file and delete it after sending
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# This code should be appended to routes/files.py

@files_bp.route('/containers/upcoming-appointments', methods=['GET'])
@require_token
def get_containers_with_upcoming_appointments():
    """
    Get containers with available appointments in the next N days
    
    Query params:
    - days: number of days to look ahead (default: 3)
    
    Response:
    {
        "success": true,
        "days_ahead": 3,
        "cutoff_date": "2025-10-14 12:00:00",
        "containers": [
            {
                "container_number": "MSCU5165756",
                "query_id": "q_1_1759809697",
                "earliest_appointment": "10/13/2025",
                "earliest_appointment_datetime": "2025-10-13 08:00:00",
                "available_slots_in_window": 12,
                "total_available_slots": 27,
                "slots_within_window": [
                    "Monday 10/13/2025 08:00 - 09:00",
                    "Monday 10/13/2025 09:00 - 10:00",
                    ...
                ],
                "screenshot_url": "/files/queries/q_1_1759809697/screenshots/file.png",
                "response_url": "/files/queries/q_1_1759809697/responses/file.json",
                "full_appointment_details": {...}
            }
        ],
        "total_containers": 5
    }
    """
    user = g.current_user
    
    try:
        # Get days parameter (default 3)
        days = int(request.args.get('days', 3))
        
        # Calculate cutoff date
        cutoff_date = datetime.now() + timedelta(days=days)
        
        # Get all queries for this user
        queries = Query.query.filter_by(user_id=user.id).all()
        
        if not queries:
            return jsonify({'error': 'No queries found'}), 404
        
        containers_with_appointments = []
        
        # Scan all response files
        for query in queries:
            responses_dir = os.path.join(
                query.folder_path,
                'containers_checking_attempts',
                'responses'
            )
            
            if not os.path.exists(responses_dir):
                continue
            
            # Process each response file
            for filename in os.listdir(responses_dir):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(responses_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        response_data = json.load(f)
                    
                    # Extract container number from filename (format: CONTAINER_timestamp.json)
                    container_number = filename.split('_')[0]
                    
                    # Check if appointment_check exists and has available_times
                    appointment_check = response_data.get('appointment_check', {})
                    available_times = appointment_check.get('available_times', [])
                    
                    if not available_times or len(available_times) == 0:
                        continue
                    
                    # Parse and filter appointments within N days
                    earliest_date = None
                    earliest_datetime = None
                    slots_within_window = []
                    
                    for time_slot in available_times:
                        try:
                            # Format: "Monday 10/13/2025 08:00 - 09:00"
                            parts = time_slot.split()
                            if len(parts) >= 3:
                                # Remove day name if present
                                if parts[0] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                                    date_part = parts[1]
                                    time_part = parts[2]
                                else:
                                    date_part = parts[0]
                                    time_part = parts[1]
                                
                                # Parse date
                                try:
                                    appt_datetime = datetime.strptime(f"{date_part} {time_part}", "%m/%d/%Y %H:%M")
                                except:
                                    # Try with AM/PM
                                    appt_datetime = datetime.strptime(f"{date_part} {time_part} {parts[3]}", "%m/%d/%Y %I:%M %p")
                                
                                # Check if this slot is within the cutoff window
                                if appt_datetime <= cutoff_date:
                                    slots_within_window.append(time_slot)
                                    
                                    # Track earliest
                                    if earliest_datetime is None or appt_datetime < earliest_datetime:
                                        earliest_datetime = appt_datetime
                                        earliest_date = date_part
                        except Exception as e:
                            continue
                    
                    # Only include container if it has appointments within N days
                    if slots_within_window and earliest_datetime:
                        # Find screenshot file
                        screenshots_dir = os.path.join(
                            query.folder_path,
                            'containers_checking_attempts',
                            'screenshots'
                        )
                        
                        screenshot_file = None
                        if os.path.exists(screenshots_dir):
                            for ss_file in os.listdir(screenshots_dir):
                                if ss_file.startswith(container_number):
                                    screenshot_file = ss_file
                                    break
                        
                        containers_with_appointments.append({
                            'container_number': container_number,
                            'query_id': query.query_id,
                            'earliest_appointment': earliest_date,
                            'earliest_appointment_datetime': earliest_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                            'available_slots_in_window': len(slots_within_window),
                            'total_available_slots': len(available_times),
                            'slots_within_window': slots_within_window,
                            'screenshot_file': screenshot_file,
                            'screenshot_url': f"/files/queries/{query.query_id}/screenshots/{screenshot_file}" if screenshot_file else None,
                            'response_file': filename,
                            'response_url': f"/files/queries/{query.query_id}/responses/{filename}",
                            'full_appointment_details': appointment_check
                        })
                
                except Exception as e:
                    # Skip files that can't be parsed
                    continue
        
        # Sort by earliest appointment
        containers_with_appointments.sort(key=lambda x: x['earliest_appointment_datetime'])
        
        return jsonify({
            'success': True,
            'days_ahead': days,
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
            'containers': containers_with_appointments,
            'total_containers': len(containers_with_appointments)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/filtered-containers/all', methods=['GET'])
@require_token
def get_all_filtered_containers():
    """
    Get all filtered_containers.xlsx files from all queries and merge them.
    If a container appears multiple times, keep only the latest occurrence.
    
    Response:
    - Returns Excel file with all unique containers (latest version of each)
    """
    user = g.current_user
    
    try:
        import pandas as pd
        
        # Get all completed queries for this user
        queries = Query.query.filter_by(
            user_id=user.id,
            status='completed'
        ).order_by(Query.started_at.desc()).all()
        
        if not queries:
            return jsonify({
                'error': 'No completed queries found',
                'message': 'Please run a query first (option 12 in menu) and wait for it to complete'
            }), 404
        
        all_containers = []
        container_tracking = {}  # Track latest occurrence of each container
        
        for query in queries:
            filtered_file = os.path.join(query.folder_path, 'filtered_containers.xlsx')
            
            if os.path.exists(filtered_file):
                try:
                    # Read filtered containers
                    df = pd.read_excel(filtered_file, engine='openpyxl', keep_default_na=False)
                    
                    # Process each container
                    for idx, row in df.iterrows():
                        container_num = str(row.get('Container #', '')).strip()
                        
                        if container_num:
                            # Check if we've seen this container before
                            if container_num not in container_tracking:
                                # First time seeing this container
                                container_tracking[container_num] = {
                                    'row': row.to_dict(),
                                    'query_timestamp': query.started_at,
                                    'query_id': query.query_id
                                }
                            else:
                                # We've seen this container before - keep the latest one
                                existing = container_tracking[container_num]
                                if query.started_at > existing['query_timestamp']:
                                    # This occurrence is newer
                                    container_tracking[container_num] = {
                                        'row': row.to_dict(),
                                        'query_timestamp': query.started_at,
                                        'query_id': query.query_id
                                    }
                
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        if not container_tracking:
            return jsonify({
                'error': 'No filtered containers found',
                'message': f'Checked {len(queries)} completed queries but no filtered_containers.xlsx files found',
                'queries_checked': len(queries)
            }), 404
        
        # Build the merged dataframe with only latest occurrences
        merged_rows = [item['row'] for item in container_tracking.values()]
        merged_df = pd.DataFrame(merged_rows)
        
        # Save to temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        merged_df.to_excel(temp_path, index=False, engine='openpyxl')
        
        return send_file(
            temp_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='all_filtered_containers_merged.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@files_bp.route('/filtered-containers/latest', methods=['GET'])
@require_token
def get_latest_filtered_containers():
    """
    Get the latest filtered_containers.xlsx file.
    
    Response:
    - Returns the most recent filtered_containers.xlsx file
    """
    user = g.current_user
    
    try:
        # Get the most recent completed query first
        query = Query.query.filter_by(
            user_id=user.id,
            status='completed'
        ).order_by(Query.started_at.desc()).first()
        
        # If no completed queries, get the most recent query regardless of status
        if not query:
            query = Query.query.filter_by(user_id=user.id).order_by(Query.started_at.desc()).first()
            
            if not query:
                return jsonify({
                    'error': 'No queries found',
                    'message': 'Please run a query first (option 12 in menu)'
                }), 404
            
            # Query exists but not completed
            return jsonify({
                'error': 'Latest query not completed',
                'query_id': query.query_id,
                'status': query.status,
                'message': f'Latest query ({query.query_id}) is {query.status}. Please wait for it to complete or run a new query.'
            }), 404
        
        filtered_file = os.path.join(query.folder_path, 'filtered_containers.xlsx')
        
        if not os.path.exists(filtered_file):
            return jsonify({
                'error': 'Filtered containers file not found',
                'query_id': query.query_id,
                'status': query.status,
                'folder_path': query.folder_path,
                'message': f'Query {query.query_id} completed but filtered_containers.xlsx not found in folder'
            }), 404
        
        return send_file(
            filtered_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'filtered_containers_latest_{query.query_id}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

