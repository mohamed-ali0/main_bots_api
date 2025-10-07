from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, query_service, app):
        self.scheduler = BackgroundScheduler()
        self.query_service = query_service
        self.app = app
    
    def start(self):
        """Start the scheduler"""
        # Run every hour
        self.scheduler.add_job(
            func=self.run_scheduled_queries,
            trigger=IntervalTrigger(minutes=60),
            id='scheduled_queries',
            name='Run scheduled queries for all users',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started - running queries every 60 minutes")
    
    def run_scheduled_queries(self):
        """Execute queries for all users with schedule enabled"""
        from models import User
        
        # Run within application context
        with self.app.app_context():
            logger.info("Running scheduled queries...")
            
            users = User.query.filter_by(schedule_enabled=True).all()
            logger.info(f"Found {len(users)} users with scheduling enabled")
            
            for user in users:
                try:
                    logger.info(f"Starting query for user {user.username}")
                    query_id = self.query_service.execute_query(user)
                    logger.info(f"Query {query_id} completed for user {user.username}")
                except Exception as e:
                    logger.error(f"Failed to execute query for user {user.username}: {e}")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")

