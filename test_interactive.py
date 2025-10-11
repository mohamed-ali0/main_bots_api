"""
Interactive Test Suite for E-Modal Management System
Choose which endpoints to test with full control
"""

import requests
import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = 'http://37.60.243.201:5000'
ADMIN_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin-dev-key-123')

# Load user info
USER_TOKEN = None
USER_ID = None

if os.path.exists('user_info.json'):
    with open('user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        USER_TOKEN = user_info.get('token')
        USER_ID = user_info.get('user_id')


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_response(response):
    """Pretty print response"""
    try:
        data = response.json()
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(data, indent=2))
    except:
        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        if 'json' in response.headers.get('Content-Type', ''):
            print(response.text)
        else:
            print(f"Content-Length: {len(response.content)} bytes")


def test_health():
    """Test: Health Check"""
    print_header("Health Check")
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=2400)
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_root():
    """Test: Root Endpoint"""
    print_header("Root Endpoint")
    try:
        response = requests.get(f'{BASE_URL}/', timeout=2400)
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_list_users():
    """Test: List All Users"""
    print_header("List All Users")
    try:
        response = requests.get(
            f'{BASE_URL}/admin/users',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_user():
    """Test: Get User Details"""
    print_header("Get User Details")
    
    if not USER_ID:
        print("[ERROR] No user ID available. Run add_user.py first.")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/admin/users/{USER_ID}',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_create_user():
    """Test: Create Test User"""
    print_header("Create Test User")
    
    username = input("Enter username [testuser]: ").strip() or 'testuser'
    password = input("Enter password [testpass123]: ").strip() or 'testpass123'
    name = input("Enter name [Test User]: ").strip() or 'Test User'
    
    user_data = {
        'name': name,
        'username': username,
        'password': password,
        'emodal_username': 'test_emodal',
        'emodal_password': 'test_pass',
        'emodal_captcha_key': 'test_key_12345'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/admin/users',
            headers={'X-Admin-Key': ADMIN_KEY},
            json=user_data,
            timeout=2400
        )
        print_response(response)
        return response.status_code == 201
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_update_credentials():
    """Test: Update User Credentials"""
    print_header("Update User Credentials")
    
    user_id = input(f"Enter user ID [{USER_ID}]: ").strip() or USER_ID
    if not user_id:
        print("[ERROR] No user ID provided")
        return False
    
    update_data = {
        'platform': 'emodal',
        'credentials': {
            'username': 'updated_username',
            'password': 'updated_password',
            'captcha_api_key': 'updated_key_123'
        }
    }
    
    try:
        response = requests.put(
            f'{BASE_URL}/admin/users/{user_id}/credentials',
            headers={'X-Admin-Key': ADMIN_KEY},
            json=update_data,
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_delete_user():
    """Test: Delete User"""
    print_header("Delete User")
    
    user_id = input("Enter user ID to delete: ").strip()
    if not user_id:
        print("[ERROR] No user ID provided")
        return False
    
    confirm = input(f"[WARNING] Delete user {user_id} and ALL data? (yes/no): ").strip()
    if confirm.lower() != 'yes':
        print("[INFO] Cancelled")
        return False
    
    try:
        response = requests.delete(
            f'{BASE_URL}/admin/users/{user_id}/flush',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_schedule():
    """Test: Get Schedule Settings"""
    print_header("Get Schedule Settings")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/schedule',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_update_schedule():
    """Test: Update Schedule Settings"""
    print_header("Update Schedule Settings")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    enabled = input("Enable schedule? (yes/no) [yes]: ").strip().lower() or 'yes'
    frequency = input("Frequency in minutes [120]: ").strip() or '120'
    
    update_data = {
        'enabled': enabled == 'yes',
        'frequency': int(frequency)
    }
    
    try:
        response = requests.put(
            f'{BASE_URL}/schedule',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            json=update_data,
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_pause_schedule():
    """Test: Pause Schedule"""
    print_header("Pause Schedule")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    try:
        response = requests.post(
            f'{BASE_URL}/schedule/pause',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_resume_schedule():
    """Test: Resume Schedule"""
    print_header("Resume Schedule")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    try:
        response = requests.post(
            f'{BASE_URL}/schedule/resume',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_trigger_query():
    """Test: Trigger Manual Query"""
    print_header("Trigger Manual Query")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    platform = input("Platform [emodal]: ").strip() or 'emodal'
    
    confirm = input(f"[WARNING] This will trigger a real {platform.upper()} query. Continue? (yes/no): ").strip()
    if confirm.lower() != 'yes':
        print("[INFO] Cancelled")
        return False
    
    try:
        response = requests.post(
            f'{BASE_URL}/queries/trigger',
            headers={
                'Authorization': f'Bearer {USER_TOKEN}',
                'Content-Type': 'application/json'
            },
            json={'platform': platform},
            timeout=2400  # 40 minutes timeout for query
        )
        print_response(response)
        return response.status_code == 202
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_list_queries():
    """Test: List Queries"""
    print_header("List Queries")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    status_filter = input("Filter by status (pending/in_progress/completed/failed) or press Enter for all: ").strip()
    limit = input("Limit [50]: ").strip() or '50'
    
    url = f'{BASE_URL}/queries?limit={limit}'
    if status_filter:
        url += f'&status={status_filter}'
    
    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_query():
    """Test: Get Query Details"""
    print_header("Get Query Details")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    query_id = input("Enter query ID: ").strip()
    if not query_id:
        print("[ERROR] No query ID provided")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries/{query_id}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_download_query():
    """Test: Download Query as ZIP"""
    print_header("Download Query as ZIP")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    query_id = input("Enter query ID: ").strip()
    if not query_id:
        print("[ERROR] No query ID provided")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries/{query_id}/download',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            filename = f"{query_id}.zip"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"\n[SUCCESS] Downloaded to {filename}")
            print(f"Size: {len(response.content) / 1024:.2f} KB")
            return True
        else:
            print_response(response)
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_delete_query():
    """Test: Delete Query"""
    print_header("Delete Query")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    query_id = input("Enter query ID to delete: ").strip()
    if not query_id:
        print("[ERROR] No query ID provided")
        return False
    
    confirm = input(f"[WARNING] Delete query {query_id} and all data? (yes/no): ").strip()
    if confirm.lower() != 'yes':
        print("[INFO] Cancelled")
        return False
    
    try:
        response = requests.delete(
            f'{BASE_URL}/queries/{query_id}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_containers():
    """Test: Get Latest Containers"""
    print_header("Get Latest Containers File")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/containers',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] File info retrieved")
            print(f"Filename: {data.get('filename')}")
            print(f"File size: {data.get('file_size') / 1024:.2f} KB")
            print(f"Last modified: {data.get('last_modified')}")
            print(f"\nDownload URL: {data.get('download_url')}")
            print(f"Note: {data.get('note')}")
            
            # Offer to download
            download = input("\nDownload file now? (yes/no): ").strip().lower()
            if download in ['yes', 'y']:
                download_url = data.get('download_url')
                dl_response = requests.get(
                    download_url,
                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                    timeout=2400
                )
                if dl_response.status_code == 200:
                    filename = data.get('filename', 'all_containers.xlsx')
                    with open(filename, 'wb') as f:
                        f.write(dl_response.content)
                    print(f"[SUCCESS] Downloaded to {filename}")
                else:
                    print(f"[ERROR] Download failed: HTTP {dl_response.status_code}")
            return True
        else:
            print_response(response)
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_appointments():
    """Test: Get Latest Appointments"""
    print_header("Get Latest Appointments File")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/appointments',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] File info retrieved")
            print(f"Filename: {data.get('filename')}")
            print(f"File size: {data.get('file_size') / 1024:.2f} KB")
            print(f"Last modified: {data.get('last_modified')}")
            print(f"\nDownload URL: {data.get('download_url')}")
            print(f"Note: {data.get('note')}")
            
            # Offer to download
            download = input("\nDownload file now? (yes/no): ").strip().lower()
            if download in ['yes', 'y']:
                download_url = data.get('download_url')
                dl_response = requests.get(
                    download_url,
                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                    timeout=2400
                )
                if dl_response.status_code == 200:
                    filename = data.get('filename', 'all_appointments.xlsx')
                    with open(filename, 'wb') as f:
                        f.write(dl_response.content)
                    print(f"[SUCCESS] Downloaded to {filename}")
                else:
                    print(f"[ERROR] Download failed: HTTP {dl_response.status_code}")
            return True
        else:
            print_response(response)
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_update_containers():
    """Test: Update Containers File"""
    print_header("Update Containers File")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    platform = input("Platform [emodal]: ").strip() or 'emodal'
    
    confirm = input(f"[WARNING] This will fetch fresh containers from {platform.upper()}. Continue? (yes/no): ").strip()
    if confirm.lower() != 'yes':
        print("[INFO] Cancelled")
        return False
    
    force_new = input(f"Force new {platform.upper()} session? (yes/no) [no]: ").strip().lower() == 'yes'
    
    try:
        print(f"\n[INFO] Fetching containers from {platform.upper()}...")
        print("[INFO] This may take several minutes...")
        
        response = requests.post(
            f'{BASE_URL}/files/containers/update',
            headers={
                'Authorization': f'Bearer {USER_TOKEN}',
                'Content-Type': 'application/json'
            },
            json={
                'platform': platform,
                'force_new_session': force_new
            },
            timeout=2400  # 40 minutes timeout
        )
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out (>10 minutes)")
        print("[INFO] Operation may still be running on server")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_update_appointments():
    """Test: Update Appointments File"""
    print_header("Update Appointments File")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    platform = input("Platform [emodal]: ").strip() or 'emodal'
    
    confirm = input(f"[WARNING] This will fetch fresh appointments from {platform.upper()}. Continue? (yes/no): ").strip()
    if confirm.lower() != 'yes':
        print("[INFO] Cancelled")
        return False
    
    force_new = input(f"Force new {platform.upper()} session? (yes/no) [no]: ").strip().lower() == 'yes'
    
    try:
        print(f"\n[INFO] Fetching appointments from {platform.upper()}...")
        print("[INFO] This may take several minutes...")
        
        response = requests.post(
            f'{BASE_URL}/files/appointments/update',
            headers={
                'Authorization': f'Bearer {USER_TOKEN}',
                'Content-Type': 'application/json'
            },
            json={
                'platform': platform,
                'force_new_session': force_new
            },
            timeout=2400  # 40 minutes timeout
        )
        print_response(response)
        return response.status_code == 200
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out (>10 minutes)")
        print("[INFO] Operation may still be running on server")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_query_files():
    """Test: Get Query-Specific Files"""
    print_header("Get Query-Specific Files")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available")
        return False
    
    query_id = input("Enter query ID: ").strip()
    if not query_id:
        print("[ERROR] No query ID provided")
        return False
    
    print("\nWhich file?")
    print("  1. All containers")
    print("  2. Filtered containers")
    print("  3. All appointments")
    
    choice = input("\nChoice (1-3): ").strip()
    
    endpoints = {
        '1': 'all-containers',
        '2': 'filtered-containers',
        '3': 'all-appointments'
    }
    
    endpoint = endpoints.get(choice)
    if not endpoint:
        print("[ERROR] Invalid choice")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/queries/{query_id}/{endpoint}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] File info retrieved")
            print(f"Filename: {data.get('filename')}")
            print(f"File size: {data.get('file_size') / 1024:.2f} KB")
            print(f"Last modified: {data.get('last_modified')}")
            print(f"Query ID: {data.get('query_id')}")
            print(f"\nDownload URL: {data.get('download_url')}")
            print(f"Note: {data.get('note')}")
            
            # Offer to download
            download = input("\nDownload file now? (yes/no): ").strip().lower()
            if download in ['yes', 'y']:
                download_url = data.get('download_url')
                dl_response = requests.get(
                    download_url,
                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                    timeout=2400
                )
                if dl_response.status_code == 200:
                    filename = data.get('filename')
                    with open(filename, 'wb') as f:
                        f.write(dl_response.content)
                    print(f"[SUCCESS] Downloaded to {filename}")
                else:
                    print(f"[ERROR] Download failed: HTTP {dl_response.status_code}")
            return True
        else:
            print_response(response)
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def show_main_menu():
    """Show main menu"""
    print_header("E-MODAL MANAGEMENT SYSTEM - INTERACTIVE TESTS")
    
    if USER_TOKEN:
        print(f"[INFO] Logged in as User ID: {USER_ID}")
        print(f"[INFO] Token: {USER_TOKEN[:20]}...")
    else:
        print("[WARNING] No user token loaded. Admin tests only available.")
    
    print("\n" + "=" * 80)
    print("SYSTEM TESTS")
    print("=" * 80)
    print("  1. Health Check")
    print("  2. Root Endpoint")
    
    print("\n" + "=" * 80)
    print("ADMIN TESTS (Requires Admin Key)")
    print("=" * 80)
    print("  3. List All Users")
    print("  4. Get User Details")
    print("  5. Create Test User")
    print("  6. Update User Credentials")
    print("  7. Delete User")
    
    print("\n" + "=" * 80)
    print("SCHEDULE TESTS (Requires User Token)")
    print("=" * 80)
    print("  8. Get Schedule Settings")
    print("  9. Update Schedule Settings")
    print(" 10. Pause Schedule")
    print(" 11. Resume Schedule")
    
    print("\n" + "=" * 80)
    print("QUERY TESTS (Requires User Token)")
    print("=" * 80)
    print(" 12. Trigger Manual Query")
    print(" 13. List Queries")
    print(" 14. Get Query Details")
    print(" 15. Download Query ZIP")
    print(" 16. Delete Query")
    
    print("\n" + "=" * 80)
    print("FILE TESTS (Requires User Token)")
    print("=" * 80)
    print(" 17. Get Latest Containers File")
    print(" 18. Get Latest Appointments File")
    print(" 19. Get Query-Specific Files")
    print(" 20. Update Containers File (Fetch from E-Modal)")
    print(" 21. Update Appointments File (Fetch from E-Modal)")
    
    print("\n" + "=" * 80)
    print("CONTAINER FILE SEARCH (Requires User Token)")
    print("=" * 80)
    print(" 24. Get All Screenshots for Container (ZIP)")
    print(" 25. Get All Responses for Container (ZIP)")
    print(" 26. Get Containers with Upcoming Appointments")
    
    print("\n" + "=" * 80)
    print("FILTERED CONTAINERS (Requires User Token)")
    print("=" * 80)
    print(" 27. Get All Filtered Containers (Merged from all queries)")
    print(" 28. Get Latest Filtered Containers")
    
    print("\n" + "=" * 80)
    print("UTILITIES")
    print("=" * 80)
    print(" 22. Run All Tests")
    print(" 23. Show Configuration")
    print("  0. Exit")
    
    print("\n" + "=" * 80)
    
    choice = input("\nEnter your choice (0-28): ").strip()
    return choice


def test_get_container_screenshots():
    """Test: Get All Screenshots for Container"""
    print_header("Get All Screenshots for Container")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available.")
        return False
    
    container_number = input("\nEnter container number (e.g., MSCU5165756): ").strip()
    
    if not container_number:
        print("[ERROR] Container number is required")
        return False
    
    print(f"\n[INFO] Fetching all screenshots for container: {container_number}")
    print("[INFO] Searching across all queries...")
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/containers/{container_number}/screenshots',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] Screenshot archive info retrieved")
            print(f"Filename: {data.get('filename')}")
            print(f"File size: {data.get('file_size') / 1024:.2f} KB")
            print(f"Screenshots count: {data.get('screenshots_count')}")
            print(f"Queries included: {data.get('queries_included')}")
            print(f"\nDownload URL: {data.get('download_url')}")
            print(f"Note: {data.get('note')}")
            
            # Offer to download
            download = input("\nDownload ZIP file now? (yes/no): ").strip().lower()
            if download in ['yes', 'y']:
                download_url = data.get('download_url')
                dl_response = requests.get(
                    download_url,
                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                    timeout=2400
                )
                if dl_response.status_code == 200:
                    filename = data.get('filename')
                    with open(filename, 'wb') as f:
                        f.write(dl_response.content)
                    print(f"[SUCCESS] Downloaded to {filename}")
                else:
                    print(f"[ERROR] Download failed: HTTP {dl_response.status_code}")
            return True
        else:
            print_response(response)
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_container_responses():
    """Test: Get All Responses for Container"""
    print_header("Get All Responses for Container")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available.")
        return False
    
    container_number = input("\nEnter container number (e.g., MSCU5165756): ").strip()
    
    if not container_number:
        print("[ERROR] Container number is required")
        return False
    
    print(f"\n[INFO] Fetching all response files for container: {container_number}")
    print("[INFO] Searching across all queries...")
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/containers/{container_number}/responses',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] Response archive info retrieved")
            print(f"Filename: {data.get('filename')}")
            print(f"File size: {data.get('file_size') / 1024:.2f} KB")
            print(f"Responses count: {data.get('responses_count')}")
            print(f"Queries included: {data.get('queries_included')}")
            print(f"\nDownload URL: {data.get('download_url')}")
            print(f"Note: {data.get('note')}")
            
            # Offer to download
            download = input("\nDownload ZIP file now? (yes/no): ").strip().lower()
            if download in ['yes', 'y']:
                download_url = data.get('download_url')
                dl_response = requests.get(
                    download_url,
                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                    timeout=2400
                )
                if dl_response.status_code == 200:
                    filename = data.get('filename')
                    with open(filename, 'wb') as f:
                        f.write(dl_response.content)
                    print(f"[SUCCESS] Downloaded to {filename}")
                else:
                    print(f"[ERROR] Download failed: HTTP {dl_response.status_code}")
            return True
        else:
            print_response(response)
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_upcoming_appointments():
    """Test: Get Containers with Upcoming Appointments"""
    print_header("Get Containers with Upcoming Appointments")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available.")
        return False
    
    days = input("\nEnter number of days to look ahead (default: 3): ").strip()
    
    if not days:
        days = 3
    else:
        try:
            days = int(days)
        except:
            print("[ERROR] Invalid number")
            return False
    
    print(f"\n[INFO] Searching for containers with appointments in the next {days} days...")
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/containers/upcoming-appointments?days={days}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n[SUCCESS] Found {data.get('total_containers', 0)} containers")
            print(f"[INFO] Days ahead: {data.get('days_ahead')}")
            print(f"[INFO] Cutoff date: {data.get('cutoff_date')}")
            
            containers = data.get('containers', [])
            if containers:
                print(f"\n{'='*80}")
                print("CONTAINERS WITH UPCOMING APPOINTMENTS")
                print(f"{'='*80}\n")
                
                for i, container in enumerate(containers, 1):
                    print(f"{i}. Container: {container.get('container_number')}")
                    print(f"   Query ID: {container.get('query_id')}")
                    print(f"   Type: {container.get('container_type')}")
                    print(f"   Earliest: {container.get('earliest_appointment')} ({container.get('earliest_appointment_datetime')})")
                    print(f"   Slots in window: {container.get('available_slots_in_window')}")
                    print(f"   Total slots: {container.get('total_available_slots')}")
                    
                    slots = container.get('slots_within_window', [])
                    if slots:
                        print(f"   Available times in next {days} days:")
                        for slot in slots[:5]:  # Show first 5
                            print(f"     - {slot}")
                        if len(slots) > 5:
                            print(f"     ... and {len(slots) - 5} more")
                    
                    screenshot_url = container.get('screenshot_url')
                    screenshot_filename = container.get('screenshot_filename')
                    
                    if screenshot_url:
                        print(f"   Screenshot URL: {screenshot_url}")
                    if screenshot_filename:
                        print(f"   Screenshot File: {screenshot_filename}")
                    
                    # Check for any port 5010 references (should be none)
                    container_json = json.dumps(container)
                    if ':5010' in container_json:
                        print(f"   [WARNING] Container contains port 5010 references!")
                    
                    print()
                
                # Offer to download screenshot for a specific container
                download = input("\nDownload screenshot for a container? Enter container number or 'no': ").strip()
                if download.lower() not in ['no', 'n', '']:
                    # Find the container
                    selected_container = None
                    for c in containers:
                        if c.get('container_number') == download:
                            selected_container = c
                            break
                    
                    if selected_container:
                        # Download screenshot (authentication required - our API)
                        if selected_container.get('screenshot_url'):
                            try:
                                ss_url = selected_container['screenshot_url']
                                print(f"[INFO] Downloading from: {ss_url}")
                                ss_response = requests.get(
                                    ss_url, 
                                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                                    timeout=30
                                )
                                
                                if ss_response.status_code == 200:
                                    ss_filename = selected_container.get('screenshot_filename', f"{download}_screenshot.png")
                                    with open(ss_filename, 'wb') as f:
                                        f.write(ss_response.content)
                                    print(f"[SUCCESS] Screenshot saved to {ss_filename}")
                                else:
                                    print(f"[ERROR] Failed to download: HTTP {ss_response.status_code}")
                            except Exception as e:
                                print(f"[ERROR] Failed to download screenshot: {e}")
                        else:
                            print("[INFO] No screenshot URL available for this container")
                    else:
                        print(f"[ERROR] Container {download} not found in results")
                
                # Show raw JSON for first container (for debugging)
                debug = input("\nShow raw JSON for first container? (yes/no): ").strip().lower()
                if debug in ['yes', 'y'] and containers:
                    print(f"\n{'='*80}")
                    print("RAW API RESPONSE (First Container)")
                    print(f"{'='*80}")
                    print(json.dumps(containers[0], indent=2))
                    print(f"{'='*80}\n")
                
                # Offer to save full response
                save = input("\nSave full JSON response to file? (yes/no): ").strip().lower()
                if save in ['yes', 'y']:
                    filename = f"upcoming_appointments_{days}days.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    print(f"[SUCCESS] Saved to {filename}")
                    print(f"\n[INFO] Screenshot URLs point to our authenticated API (port 5000)")
                    print(f"[INFO] Use Authorization header with user token to access screenshots")
                    print(f"[INFO] All files are served through our secure endpoints")
            else:
                print("\n[INFO] No containers found with appointments in the specified time window")
            
            return True
        else:
            print_response(response)
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_all_filtered_containers():
    """Test: Get All Filtered Containers (Merged)"""
    print_header("Get All Filtered Containers (Merged)")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available.")
        return False
    
    print("\n[INFO] Fetching and merging all filtered containers from all queries...")
    print("[INFO] If a container appears multiple times, only the latest version is kept.")
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/filtered-containers/all',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] Merged file info retrieved")
            print(f"Filename: {data.get('filename')}")
            print(f"File size: {data.get('file_size') / 1024:.2f} KB")
            print(f"Containers count: {data.get('containers_count')}")
            print(f"Unique containers: {data.get('unique_containers')}")
            print(f"Queries checked: {data.get('queries_checked')}")
            print(f"\nDownload URL: {data.get('download_url')}")
            print(f"Note: {data.get('note')}")
            
            # Offer to download
            download = input("\nDownload file now? (yes/no): ").strip().lower()
            if download in ['yes', 'y']:
                download_url = data.get('download_url')
                dl_response = requests.get(
                    download_url,
                    headers={'Authorization': f'Bearer {USER_TOKEN}'},
                    timeout=2400
                )
                if dl_response.status_code == 200:
                    filename = data.get('filename')
                    with open(filename, 'wb') as f:
                        f.write(dl_response.content)
                    print(f"[SUCCESS] Downloaded to {filename}")
                    
                    # Try to show summary
                    try:
                        import pandas as pd
                        df = pd.read_excel(filename, engine='openpyxl')
                        print(f"[INFO] Verified: {len(df)} rows")
                        print(f"[INFO] Columns: {', '.join(df.columns.tolist()[:5])}...")
                    except:
                        pass
                else:
                    print(f"[ERROR] Download failed: HTTP {dl_response.status_code}")
            return True
        else:
            # Show error details
            try:
                error_data = response.json()
                print(f"\n[ERROR] {error_data.get('error', 'Unknown error')}")
                if 'message' in error_data:
                    print(f"[INFO] {error_data['message']}")
                if 'queries_checked' in error_data:
                    print(f"[INFO] Queries checked: {error_data['queries_checked']}")
            except:
                print_response(response)
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_get_latest_filtered_containers():
    """Test: Get Latest Filtered Containers"""
    print_header("Get Latest Filtered Containers")
    
    if not USER_TOKEN:
        print("[ERROR] No user token available.")
        return False
    
    print("\n[INFO] Fetching the latest filtered containers file...")
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/filtered-containers/latest',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            # Extract query_id from Content-Disposition header if available
            filename = "filtered_containers_latest.xlsx"
            if 'Content-Disposition' in response.headers:
                import re
                match = re.search(r'filename="?(.+)"?', response.headers['Content-Disposition'])
                if match:
                    filename = match.group(1)
            
            # Save the Excel file
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"\n[SUCCESS] Excel file downloaded: {filename}")
            print(f"[INFO] File size: {len(response.content)} bytes")
            
            # Try to show summary
            try:
                import pandas as pd
                df = pd.read_excel(filename, engine='openpyxl')
                print(f"[INFO] Total containers: {len(df)}")
                print(f"[INFO] Columns: {', '.join(df.columns.tolist())}")
            except:
                pass
            
            return True
        else:
            # Show error details
            try:
                error_data = response.json()
                print(f"\n[ERROR] {error_data.get('error', 'Unknown error')}")
                if 'message' in error_data:
                    print(f"[INFO] {error_data['message']}")
                if 'query_id' in error_data:
                    print(f"[INFO] Latest query ID: {error_data['query_id']}")
                if 'status' in error_data:
                    print(f"[INFO] Query status: {error_data['status']}")
                if 'folder_path' in error_data:
                    print(f"[INFO] Folder path: {error_data['folder_path']}")
            except:
                print_response(response)
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def show_config():
    """Show current configuration"""
    print_header("CURRENT CONFIGURATION")
    
    print(f"Base URL:     {BASE_URL}")
    print(f"Admin Key:    {ADMIN_KEY[:20]}...")
    print(f"User Token:   {USER_TOKEN[:20] if USER_TOKEN else 'Not loaded'}...")
    print(f"User ID:      {USER_ID or 'Not loaded'}")
    
    if os.path.exists('user_info.json'):
        with open('user_info.json', 'r', encoding='utf-8') as f:
            user_info = json.load(f)
            print(f"\nUser Info:")
            print(f"  Username:       {user_info.get('username')}")
            print(f"  E-Modal User:   {user_info.get('emodal_username')}")
            print(f"  Session ID:     {user_info.get('session_id', 'Not set')}")
    
    if os.path.exists('.env'):
        print(f"\n[INFO] .env file exists")
        print(f"[INFO] Database: {os.getenv('DATABASE_URL', 'Not configured')}")
        print(f"[INFO] E-Modal API: {os.getenv('EMODAL_API_URL', 'Not configured')}")
    
    if os.path.exists('emodal.db'):
        size = os.path.getsize('emodal.db') / 1024
        print(f"\n[INFO] Database file: emodal.db ({size:.2f} KB)")


def run_all_tests():
    """Run all tests sequentially"""
    print_header("RUNNING ALL TESTS")
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("List Users", test_list_users),
        ("Get User", test_get_user),
        ("Get Schedule", test_get_schedule),
        ("List Queries", test_list_queries),
        ("Get Containers", test_get_containers),
        ("Get Appointments", test_get_appointments),
    ]
    
    results = {'passed': 0, 'failed': 0}
    
    for name, test_func in tests:
        print(f"\n[TEST] {name}...")
        try:
            result = test_func()
            if result:
                results['passed'] += 1
                print(f"[PASS] {name}")
            else:
                results['failed'] += 1
                print(f"[FAIL] {name}")
        except Exception as e:
            results['failed'] += 1
            print(f"[FAIL] {name} - {e}")
        
        time.sleep(1)  # Small delay between tests
    
    print_header("TEST RESULTS")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total:  {results['passed'] + results['failed']}")


def main():
    """Main interactive loop"""
    
    test_functions = {
        '1': test_health,
        '2': test_root,
        '3': test_list_users,
        '4': test_get_user,
        '5': test_create_user,
        '6': test_update_credentials,
        '7': test_delete_user,
        '8': test_get_schedule,
        '9': test_update_schedule,
        '10': test_pause_schedule,
        '11': test_resume_schedule,
        '12': test_trigger_query,
        '13': test_list_queries,
        '14': test_get_query,
        '15': test_download_query,
        '16': test_delete_query,
        '17': test_get_containers,
        '18': test_get_appointments,
        '19': test_get_query_files,
        '20': test_update_containers,
        '21': test_update_appointments,
        '22': run_all_tests,
        '23': show_config,
        '24': test_get_container_screenshots,
        '25': test_get_container_responses,
        '26': test_get_upcoming_appointments,
        '27': test_get_all_filtered_containers,
        '28': test_get_latest_filtered_containers,
    }
    
    while True:
        choice = show_main_menu()
        
        if choice == '0':
            print("\n[INFO] Goodbye!")
            break
        elif choice in test_functions:
            test_functions[choice]()
            input("\nPress Enter to continue...")
        else:
            print("[ERROR] Invalid choice")
            time.sleep(1)


if __name__ == '__main__':
    main()

