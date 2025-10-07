import os
import json
import logging

logger = logging.getLogger(__name__)

class FileService:
    """Handle file operations for users"""
    
    @staticmethod
    def create_user_folders(user):
        """Create complete folder structure for user"""
        from utils.constants import PLATFORMS
        
        for platform in PLATFORMS:
            platform_path = os.path.join(user.folder_path, platform)
            os.makedirs(platform_path, exist_ok=True)
            
            # Create queries folder for emodal
            if platform == 'emodal':
                queries_path = os.path.join(platform_path, 'queries')
                os.makedirs(queries_path, exist_ok=True)
        
        logger.info(f"Created folder structure for user {user.username}")
    
    @staticmethod
    def create_user_credentials(user, data):
        """Create user_cre_env.json file"""
        creds = {
            'emodal': {
                'username': data.get('emodal_username', ''),
                'password': data.get('emodal_password', ''),
                'captcha_api_key': data.get('emodal_captcha_key', '')
            },
            'apmt': {},
            'wbct': {},
            'fms': {},
            'yti': {},
            'lbct': {}
        }
        
        creds_file = os.path.join(user.folder_path, 'user_cre_env.json')
        with open(creds_file, 'w') as f:
            json.dump(creds, f, indent=2)
        
        logger.info(f"Created credentials file for user {user.username}")
    
    @staticmethod
    def load_user_credentials(user):
        """Load user_cre_env.json"""
        creds_file = os.path.join(user.folder_path, 'user_cre_env.json')
        with open(creds_file, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def create_query_folders(query_folder):
        """Create folder structure for query"""
        os.makedirs(os.path.join(query_folder, 'containers_checking_attempts', 'screenshots'), exist_ok=True)
        os.makedirs(os.path.join(query_folder, 'containers_checking_attempts', 'responses'), exist_ok=True)
        logger.info(f"Created query folder structure at {query_folder}")

