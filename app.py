from flask import Flask, jsonify
from flask_migrate import Migrate
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# Import db from models
from models.base import db

# Initialize extensions
migrate = Migrate()

# Global services
emodal_client = None
query_service = None
scheduler_service = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Setup logging
    setup_logging(app)
    
    # Create storage directory
    os.makedirs(app.config['STORAGE_PATH'], exist_ok=True)
    
    with app.app_context():
        # Import models (after db initialization)
        from models import User, Query
        
        # Initialize services
        global emodal_client, query_service, scheduler_service
        
        from services.emodal_client import EModalClient
        from services.query_service import QueryService
        from services.scheduler_service import SchedulerService
        
        emodal_client = EModalClient(app.config['EMODAL_API_URL'])
        query_service = QueryService(emodal_client)
        scheduler_service = SchedulerService(query_service, app)
        
        # Store services in app config for routes to access
        app.config['QUERY_SERVICE'] = query_service
        app.config['EMODAL_CLIENT'] = emodal_client
        
        # Register blueprints
        from routes.admin import admin_bp
        from routes.queries import queries_bp
        from routes.files import files_bp
        from routes.schedule import schedule_bp
        
        app.register_blueprint(admin_bp)
        app.register_blueprint(queries_bp)
        app.register_blueprint(files_bp)
        app.register_blueprint(schedule_bp)
        
        # Health check endpoint
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'service': 'E-Modal Management System',
                'scheduler': 'running' if scheduler_service.scheduler.running else 'stopped',
                'database': 'connected'
            })
        
        # Root endpoint
        @app.route('/', methods=['GET'])
        def root():
            return jsonify({
                'service': 'E-Modal Management System',
                'version': '1.0.0',
                'status': 'running',
                'endpoints': {
                    'health': '/health',
                    'admin': '/admin/*',
                    'queries': '/queries/*',
                    'files': '/files/*',
                    'schedule': '/schedule/*'
                }
            })
        
        # Debug: List all routes
        @app.route('/routes', methods=['GET'])
        def list_routes():
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'path': str(rule)
                })
            return jsonify({'routes': sorted(routes, key=lambda x: x['path'])})

        
        # Error handlers
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            app.logger.error(f'Internal error: {error}')
            return jsonify({'error': 'Internal server error'}), 500
        
        # Start scheduler
        try:
            scheduler_service.start()
            app.logger.info('Scheduler started successfully')
        except Exception as e:
            app.logger.error(f'Failed to start scheduler: {e}')
    
    return app


def setup_logging(app):
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # File handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240000,
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('E-Modal Management System startup')


if __name__ == '__main__':
    app = create_app()
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG'],
        use_reloader=False  # Disable reloader to prevent threading issues
    )

