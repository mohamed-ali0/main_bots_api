from flask import Blueprint, request, jsonify, g, send_file
from models import db, Query
from utils.decorators import require_token
import os
import zipfile
import io
import shutil
import threading

queries_bp = Blueprint('queries', __name__, url_prefix='/queries')

@queries_bp.route('/trigger', methods=['POST'])
@require_token
def trigger_query():
    """
    Manually trigger a query for current user (asynchronous - returns immediately)
    
    Request (optional):
    {
        "platform": "emodal"  // default: "emodal"
    }
    
    Response (200 OK - immediate):
    {
        "success": true,
        "query_id": "q_1_1696789012",
        "platform": "emodal",
        "message": "Query triggered successfully",
        "status": "pending",
        "next_scheduled_run": "2025-10-11 15:30:00",
        "note": "Query is running in background. Use GET /queries/{query_id} to check status."
    }
    """
    user = g.current_user
    
    # Get platform from request body (default: emodal)
    data = request.get_json() or {}
    platform = data.get('platform', 'emodal')
    
    # Get services from app context
    from flask import current_app
    query_service = current_app.config['QUERY_SERVICE']
    scheduler_service = current_app.config.get('SCHEDULER_SERVICE')
    
    # Create query record first to get query_id
    import time
    query_id = f"q_{user.id}_{int(time.time())}"
    
    # Create initial query record in database
    query = Query(
        query_id=query_id,
        user_id=user.id,
        platform=platform,
        status='pending',
        folder_path=query_service._get_query_folder_path(user.id, query_id)
    )
    db.session.add(query)
    db.session.commit()
    
    # Get Flask app for thread context
    app = current_app._get_current_object()
    
    # Execute query in background thread (non-blocking)
    def run_query_async():
        try:
            # Need to work with Flask app context for database access
            with app.app_context():
                from services.file_service import FileService
                from datetime import datetime
                
                # Reload query from database (needed in new thread context)
                query_obj = Query.query.filter_by(query_id=query_id).first()
                if not query_obj:
                    return
                
                # Create folder structure
                FileService.create_query_folders(query_obj.folder_path)
                
                # Update status to in_progress
                query_obj.status = 'in_progress'
                db.session.commit()
                
                # Ensure user has active session
                user_obj = query_obj.user  # Get user from relationship
                session_id = query_service._ensure_session(user_obj, current_query_id=query_id)
                
                # Execute query steps
                summary_stats = query_service._execute_query_steps(user_obj, query_obj, session_id)
                
                # Mark as completed
                query_obj.status = 'completed'
                query_obj.summary_stats = summary_stats
                query_obj.completed_at = datetime.utcnow()
                db.session.commit()
                
        except Exception as e:
            # Mark as failed
            try:
                with app.app_context():
                    from datetime import datetime
                    query_obj = Query.query.filter_by(query_id=query_id).first()
                    if query_obj:
                        query_obj.status = 'failed'
                        query_obj.error_message = str(e)
                        query_obj.completed_at = datetime.utcnow()
                        db.session.commit()
            except:
                pass
            
            import logging
            logging.error(f"Background query execution failed: {e}")
    
    # Start background thread
    thread = threading.Thread(target=run_query_async, daemon=True)
    thread.start()
    
    # Reschedule next run to 2 hours from now
    next_run_info = None
    if scheduler_service:
        scheduler_service.reschedule_after_manual_query()
        from datetime import datetime, timedelta
        next_run = datetime.now() + timedelta(hours=2)
        next_run_info = next_run.strftime('%Y-%m-%d %H:%M:%S')
    
    response = {
        'success': True,
        'query_id': query_id,
        'platform': platform,
        'message': 'Query triggered successfully',
        'status': 'pending',
        'note': f'Query is running in background. Use GET /queries/{query_id} to check status.'
    }
    
    if next_run_info:
        response['next_scheduled_run'] = next_run_info
    
    return jsonify(response), 200


@queries_bp.route('', methods=['GET'])
@require_token
def list_queries():
    """
    List user's queries with filtering
    
    Query params:
    - status: filter by status (pending, in_progress, completed, failed)
    - limit: number of results (default: 50)
    - offset: pagination offset (default: 0)
    
    Response:
    {
        "success": true,
        "queries": [...],
        "total": 100,
        "limit": 50,
        "offset": 0
    }
    """
    user = g.current_user
    
    # Get query parameters
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    # Build query
    query = Query.query.filter_by(user_id=user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    queries = query.order_by(Query.started_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        'success': True,
        'queries': [{
            'query_id': q.query_id,
            'platform': q.platform,
            'status': q.status,
            'summary_stats': q.summary_stats,
            'error_message': q.error_message,
            'started_at': q.started_at.isoformat(),
            'completed_at': q.completed_at.isoformat() if q.completed_at else None
        } for q in queries],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@queries_bp.route('/<query_id>', methods=['GET'])
@require_token
def get_query(query_id):
    """
    Get detailed query information
    
    Response:
    {
        "success": true,
        "query": {
            "query_id": "q_1_1696789012",
            "status": "completed",
            "summary_stats": {...},
            "started_at": "2025-10-06T12:00:00",
            "completed_at": "2025-10-06T12:20:00"
        }
    }
    """
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    return jsonify({
        'success': True,
        'query': {
            'query_id': query.query_id,
            'platform': query.platform,
            'status': query.status,
            'folder_path': query.folder_path,
            'summary_stats': query.summary_stats,
            'error_message': query.error_message,
            'started_at': query.started_at.isoformat(),
            'completed_at': query.completed_at.isoformat() if query.completed_at else None
        }
    })


@queries_bp.route('/<query_id>/download', methods=['GET'])
@require_token
def download_query(query_id):
    """
    Download entire query folder as ZIP
    
    Returns:
        ZIP file containing all query data
    """
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    if not os.path.exists(query.folder_path):
        return jsonify({'error': 'Query folder not found'}), 404
    
    # Create ZIP in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(query.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, query.folder_path)
                zf.write(file_path, arcname)
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{query_id}.zip'
    )


@queries_bp.route('/<query_id>', methods=['DELETE'])
@require_token
def delete_query(query_id):
    """Delete specific query and its data"""
    user = g.current_user
    query = Query.query.filter_by(query_id=query_id, user_id=user.id).first_or_404()
    
    # Delete folder
    if os.path.exists(query.folder_path):
        shutil.rmtree(query.folder_path)
    
    # Delete from database
    db.session.delete(query)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Query deleted'})

