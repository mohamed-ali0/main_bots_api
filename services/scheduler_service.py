from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, query_service, app):
        self.scheduler = BackgroundScheduler()
        self.query_service = query_service
        self.app = app
    
    def start(self):
        """Start the scheduler"""
        # Run every 2 hours
        self.scheduler.add_job(
            func=self.run_scheduled_queries,
            trigger=IntervalTrigger(minutes=120),
            id='scheduled_queries',
            name='Run scheduled queries for all users',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started - running queries every 120 minutes (2 hours)")
    
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
    
    def reschedule_after_manual_query(self):
        """Reschedule next query to run 2 hours from now after a manual query"""
        try:
            # Remove existing job
            self.scheduler.remove_job('scheduled_queries')
            
            # Add new job that runs 2 hours from now, then every 2 hours after that
            next_run = datetime.now() + timedelta(hours=2)
            self.scheduler.add_job(
                func=self.run_scheduled_queries,
                trigger=IntervalTrigger(minutes=120),
                id='scheduled_queries',
                name='Run scheduled queries for all users',
                replace_existing=True,
                next_run_time=next_run
            )
            
            logger.info(f"Scheduler rescheduled - next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Failed to reschedule: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")

