"""
Script to add a new user to the E-Modal Management System
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin-dev-key-123')

# User details
USER_DATA = {
    'name': 'Juan Fernandez',
    'username': 'jfernandez',
    'password': 'taffie',
    'emodal_username': 'jfernandez',
    'emodal_password': 'taffie',
    'emodal_captcha_key': '7bf85bb6f37c9799543a2a463aab2b4f'
}

# Session ID to set
SESSION_ID = 'session_1759763507_-8222151154545660229'


def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print("[OK] Server is running")
            return True
        else:
            print("[ERROR] Server returned unexpected status")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Server is not running: {e}")
        print("\nPlease start the server first:")
        print("   python app.py")
        return False


def create_user():
    """Create a new user"""
    print("\n" + "=" * 60)
    print("Creating user...")
    print("=" * 60)
    
    try:
        response = requests.post(
            f'{BASE_URL}/admin/users',
            headers={
                'X-Admin-Key': ADMIN_KEY,
                'Content-Type': 'application/json'
            },
            json=USER_DATA,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print("\n[SUCCESS] User created successfully!")
            print("\nUser Details:")
            print(f"  ID: {data['user']['id']}")
            print(f"  Name: {data['user']['name']}")
            print(f"  Username: {data['user']['username']}")
            print(f"  Token: {data['user']['token']}")
            print(f"  Folder: {data['user']['folder_path']}")
            return data['user']
        elif response.status_code == 400:
            error_data = response.json()
            if 'already exists' in str(error_data):
                print("\n[WARNING] User already exists!")
                print("Getting existing user details...")
                return get_existing_user()
            else:
                print(f"\n[ERROR] Error creating user: {error_data}")
                return None
        else:
            print(f"\n[ERROR] Failed to create user")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed: {e}")
        return None


def get_existing_user():
    """Get existing user by username"""
    try:
        # List all users to find the one we want
        response = requests.get(
            f'{BASE_URL}/admin/users',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            users = response.json()['users']
            for user in users:
                if user['username'] == USER_DATA['username']:
                    print("\n[SUCCESS] Found existing user!")
                    print(f"  ID: {user['id']}")
                    print(f"  Username: {user['username']}")
                    
                    # Get detailed user info
                    detail_response = requests.get(
                        f'{BASE_URL}/admin/users/{user["id"]}',
                        headers={'X-Admin-Key': ADMIN_KEY},
                        timeout=10
                    )
                    
                    if detail_response.status_code == 200:
                        detailed_user = detail_response.json()['user']
                        print(f"  Token: {detailed_user['token']}")
                        return detailed_user
                    
            print("[ERROR] User not found in list")
            return None
        else:
            print(f"[ERROR] Failed to get users: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return None


def set_session_id(user_id):
    """Set the E-Modal session ID for the user"""
    print(f"\n" + "=" * 60)
    print(f"Setting session ID: {SESSION_ID}")
    print("=" * 60)
    
    # Note: This requires direct database access
    # We'll provide SQL command to run manually
    
    print("\n[INFO] Session ID must be set in the database:")
    print("\nOption 1: Using flask shell")
    print("-" * 60)
    print("flask shell")
    print(">>> from models import User, db")
    print(f">>> user = User.query.get({user_id})")
    print(f">>> user.session_id = '{SESSION_ID}'")
    print(">>> db.session.commit()")
    print(">>> print('Session ID updated!')")
    print(">>> exit()")
    
    print("\nOption 2: Run the helper script (easiest)")
    print("-" * 60)
    print("python set_session.py")
    
    return True


def create_session_setter_script(user_id):
    """Create a helper script to set session ID"""
    script_content = f"""#!/usr/bin/env python
'''
Helper script to set session ID for user
'''

from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    user = User.query.get({user_id})
    if user:
        user.session_id = '{SESSION_ID}'
        db.session.commit()
        print(f'Session ID set for user {{user.username}}')
        print(f'   Session ID: {{user.session_id}}')
    else:
        print('User not found')
"""
    
    with open('set_session.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("\nCreated set_session.py")
    print("Run it with: python set_session.py")


def save_user_info(user):
    """Save user info to file for easy reference"""
    user_info = {
        'user_id': user['id'],
        'username': user['username'],
        'token': user['token'],
        'emodal_username': USER_DATA['emodal_username'],
        'emodal_password': USER_DATA['emodal_password'],
        'session_id': SESSION_ID,
        'base_url': BASE_URL
    }
    
    with open('user_info.json', 'w', encoding='utf-8') as f:
        json.dump(user_info, f, indent=2)
    
    print("\n[SUCCESS] User info saved to user_info.json")


def main():
    print("=" * 60)
    print("E-Modal Management System - Add User Script")
    print("=" * 60)
    
    # Check if server is running
    if not check_server():
        sys.exit(1)
    
    # Create or get user
    user = create_user()
    
    if not user:
        print("\n[ERROR] Failed to create/get user")
        sys.exit(1)
    
    # Provide instructions for setting session ID
    set_session_id(user['id'])
    
    # Create helper script
    create_session_setter_script(user['id'])
    
    # Save user info
    save_user_info(user)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Set session ID: python set_session.py")
    print("2. Run tests: python test_all_endpoints.py")
    print("\nUser token saved in user_info.json")
    print("=" * 60)


if __name__ == '__main__':
    main()

