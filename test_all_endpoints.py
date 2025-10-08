"""
Comprehensive Test Suite for E-Modal Management System
Tests all 22 API endpoints
"""

import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin-dev-key-123')

# Try to load user info from file
USER_TOKEN = None
USER_ID = None

if os.path.exists('user_info.json'):
    with open('user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        USER_TOKEN = user_info.get('token')
        USER_ID = user_info.get('user_id')
        print(f"[INFO] Loaded user info from user_info.json")
        print(f"   User ID: {USER_ID}")
        print(f"   Token: {USER_TOKEN[:20]}...")

# Test results tracking
test_results = {
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'total': 0,
    'details': []
}


def print_header(text, char="="):
    """Print a formatted header"""
    print(f"\n{char * 80}")
    print(f"  {text}")
    print(f"{char * 80}\n")


def print_test(test_name, status, details=""):
    """Print test result"""
    symbols = {
        'pass': '[PASS]',
        'fail': '[FAIL]',
        'skip': '[SKIP]',
        'info': '[INFO]'
    }
    
    symbol = symbols.get(status, '[?]')
    print(f"{symbol} {test_name}")
    
    if details:
        print(f"   {details}")


def record_result(test_name, passed, details="", response=None):
    """Record test result"""
    test_results['total'] += 1
    
    if passed:
        test_results['passed'] += 1
        print_test(test_name, 'pass', details)
    else:
        test_results['failed'] += 1
        print_test(test_name, 'fail', details)
    
    test_results['details'].append({
        'test': test_name,
        'passed': passed,
        'details': details,
        'response': response.json() if response and response.text else None
    })


def skip_test(test_name, reason):
    """Skip a test"""
    test_results['total'] += 1
    test_results['skipped'] += 1
    print_test(test_name, 'skip', reason)
    test_results['details'].append({
        'test': test_name,
        'passed': None,
        'details': f"SKIPPED: {reason}"
    })


# ============================================================================
# SYSTEM TESTS
# ============================================================================

def test_health_check():
    """Test 1: Health Check Endpoint"""
    print_header("Test 1: Health Check", "-")
    
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=2400)
        
        if response.status_code == 200:
            data = response.json()
            details = f"Status: {data.get('status')}, Scheduler: {data.get('scheduler')}"
            record_result("GET /health", True, details, response)
            return True
        else:
            record_result("GET /health", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("GET /health", False, f"Error: {str(e)}")
        return False


def test_root_endpoint():
    """Test 2: Root Endpoint"""
    print_header("Test 2: Root Endpoint", "-")
    
    try:
        response = requests.get(f'{BASE_URL}/', timeout=2400)
        
        if response.status_code == 200:
            data = response.json()
            record_result("GET /", True, f"Service: {data.get('service')}", response)
            return True
        else:
            record_result("GET /", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("GET /", False, f"Error: {str(e)}")
        return False


# ============================================================================
# ADMIN TESTS
# ============================================================================

def test_list_users():
    """Test 3: List All Users"""
    print_header("Test 3: List All Users", "-")
    
    try:
        response = requests.get(
            f'{BASE_URL}/admin/users',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            record_result("GET /admin/users", True, f"Found {len(users)} users", response)
            return users
        else:
            record_result("GET /admin/users", False, f"Status: {response.status_code}", response)
            return []
            
    except Exception as e:
        record_result("GET /admin/users", False, f"Error: {str(e)}")
        return []


def test_get_user(user_id):
    """Test 4: Get User Details"""
    print_header("Test 4: Get User Details", "-")
    
    if not user_id:
        skip_test("GET /admin/users/{id}", "No user ID available")
        return None
    
    try:
        response = requests.get(
            f'{BASE_URL}/admin/users/{user_id}',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            details = f"User: {user.get('username')}, Queries: {user.get('query_count')}"
            record_result(f"GET /admin/users/{user_id}", True, details, response)
            return user
        else:
            record_result(f"GET /admin/users/{user_id}", False, f"Status: {response.status_code}", response)
            return None
            
    except Exception as e:
        record_result(f"GET /admin/users/{user_id}", False, f"Error: {str(e)}")
        return None


def test_create_test_user():
    """Test 5: Create Test User"""
    print_header("Test 5: Create Test User", "-")
    
    test_user = {
        'name': 'Test User',
        'username': f'testuser_{int(time.time())}',
        'password': 'testpass123',
        'emodal_username': 'test_emodal',
        'emodal_password': 'test_pass',
        'emodal_captcha_key': 'test_key_12345'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/admin/users',
            headers={
                'X-Admin-Key': ADMIN_KEY,
                'Content-Type': 'application/json'
            },
            json=test_user,
            timeout=2400
        )
        
        if response.status_code == 201:
            data = response.json()
            user = data.get('user', {})
            record_result("POST /admin/users", True, f"Created: {user.get('username')}", response)
            return user
        else:
            record_result("POST /admin/users", False, f"Status: {response.status_code}", response)
            return None
            
    except Exception as e:
        record_result("POST /admin/users", False, f"Error: {str(e)}")
        return None


def test_update_credentials(user_id):
    """Test 6: Update User Credentials"""
    print_header("Test 6: Update User Credentials", "-")
    
    if not user_id:
        skip_test("PUT /admin/users/{id}/credentials", "No user ID available")
        return False
    
    update_data = {
        'platform': 'emodal',
        'credentials': {
            'username': 'updated_user',
            'password': 'updated_pass',
            'captcha_api_key': 'updated_key'
        }
    }
    
    try:
        response = requests.put(
            f'{BASE_URL}/admin/users/{user_id}/credentials',
            headers={
                'X-Admin-Key': ADMIN_KEY,
                'Content-Type': 'application/json'
            },
            json=update_data,
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result(f"PUT /admin/users/{user_id}/credentials", True, "Credentials updated", response)
            return True
        else:
            record_result(f"PUT /admin/users/{user_id}/credentials", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result(f"PUT /admin/users/{user_id}/credentials", False, f"Error: {str(e)}")
        return False


# ============================================================================
# SCHEDULE TESTS
# ============================================================================

def test_get_schedule():
    """Test 7: Get Schedule Settings"""
    print_header("Test 7: Get Schedule Settings", "-")
    
    if not USER_TOKEN:
        skip_test("GET /schedule", "No user token available")
        return None
    
    try:
        response = requests.get(
            f'{BASE_URL}/schedule',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            schedule = data.get('schedule', {})
            details = f"Enabled: {schedule.get('enabled')}, Frequency: {schedule.get('frequency')}min"
            record_result("GET /schedule", True, details, response)
            return schedule
        else:
            record_result("GET /schedule", False, f"Status: {response.status_code}", response)
            return None
            
    except Exception as e:
        record_result("GET /schedule", False, f"Error: {str(e)}")
        return None


def test_update_schedule():
    """Test 8: Update Schedule Settings"""
    print_header("Test 8: Update Schedule Settings", "-")
    
    if not USER_TOKEN:
        skip_test("PUT /schedule", "No user token available")
        return False
    
    update_data = {
        'enabled': True,
        'frequency': 120
    }
    
    try:
        response = requests.put(
            f'{BASE_URL}/schedule',
            headers={
                'Authorization': f'Bearer {USER_TOKEN}',
                'Content-Type': 'application/json'
            },
            json=update_data,
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            schedule = data.get('schedule', {})
            details = f"Frequency updated to {schedule.get('frequency')}min"
            record_result("PUT /schedule", True, details, response)
            return True
        else:
            record_result("PUT /schedule", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("PUT /schedule", False, f"Error: {str(e)}")
        return False


def test_pause_schedule():
    """Test 9: Pause Schedule"""
    print_header("Test 9: Pause Schedule", "-")
    
    if not USER_TOKEN:
        skip_test("POST /schedule/pause", "No user token available")
        return False
    
    try:
        response = requests.post(
            f'{BASE_URL}/schedule/pause',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result("POST /schedule/pause", True, "Schedule paused", response)
            return True
        else:
            record_result("POST /schedule/pause", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("POST /schedule/pause", False, f"Error: {str(e)}")
        return False


def test_resume_schedule():
    """Test 10: Resume Schedule"""
    print_header("Test 10: Resume Schedule", "-")
    
    if not USER_TOKEN:
        skip_test("POST /schedule/resume", "No user token available")
        return False
    
    try:
        response = requests.post(
            f'{BASE_URL}/schedule/resume',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result("POST /schedule/resume", True, "Schedule resumed", response)
            return True
        else:
            record_result("POST /schedule/resume", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("POST /schedule/resume", False, f"Error: {str(e)}")
        return False


# ============================================================================
# QUERY TESTS
# ============================================================================

def test_trigger_query():
    """Test 11: Trigger Manual Query"""
    print_header("Test 11: Trigger Manual Query", "-")
    
    if not USER_TOKEN:
        skip_test("POST /queries/trigger", "No user token available")
        return None
    
    print("[WARNING] This will trigger a real query (may take several minutes)")
    print("   The test will continue but query may complete after tests finish")
    
    try:
        response = requests.post(
            f'{BASE_URL}/queries/trigger',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 202:
            data = response.json()
            query_id = data.get('query_id')
            record_result("POST /queries/trigger", True, f"Query started: {query_id}", response)
            return query_id
        else:
            record_result("POST /queries/trigger", False, f"Status: {response.status_code}", response)
            return None
            
    except Exception as e:
        record_result("POST /queries/trigger", False, f"Error: {str(e)}")
        return None


def test_list_queries():
    """Test 12: List Queries"""
    print_header("Test 12: List Queries", "-")
    
    if not USER_TOKEN:
        skip_test("GET /queries", "No user token available")
        return []
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            queries = data.get('queries', [])
            record_result("GET /queries", True, f"Found {len(queries)} queries", response)
            return queries
        else:
            record_result("GET /queries", False, f"Status: {response.status_code}", response)
            return []
            
    except Exception as e:
        record_result("GET /queries", False, f"Error: {str(e)}")
        return []


def test_list_queries_filtered():
    """Test 13: List Queries with Filters"""
    print_header("Test 13: List Queries (Filtered)", "-")
    
    if not USER_TOKEN:
        skip_test("GET /queries?status=completed", "No user token available")
        return []
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries?status=completed&limit=10',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            queries = data.get('queries', [])
            record_result("GET /queries (filtered)", True, f"Found {len(queries)} completed queries", response)
            return queries
        else:
            record_result("GET /queries (filtered)", False, f"Status: {response.status_code}", response)
            return []
            
    except Exception as e:
        record_result("GET /queries (filtered)", False, f"Error: {str(e)}")
        return []


def test_get_query(query_id):
    """Test 14: Get Query Details"""
    print_header("Test 14: Get Query Details", "-")
    
    if not USER_TOKEN:
        skip_test("GET /queries/{id}", "No user token available")
        return None
    
    if not query_id:
        skip_test("GET /queries/{id}", "No query ID available")
        return None
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries/{query_id}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            data = response.json()
            query = data.get('query', {})
            details = f"Status: {query.get('status')}"
            record_result(f"GET /queries/{query_id}", True, details, response)
            return query
        else:
            record_result(f"GET /queries/{query_id}", False, f"Status: {response.status_code}", response)
            return None
            
    except Exception as e:
        record_result(f"GET /queries/{query_id}", False, f"Error: {str(e)}")
        return None


def test_download_query(query_id):
    """Test 15: Download Query as ZIP"""
    print_header("Test 15: Download Query as ZIP", "-")
    
    if not USER_TOKEN:
        skip_test("GET /queries/{id}/download", "No user token available")
        return False
    
    if not query_id:
        skip_test("GET /queries/{id}/download", "No query ID available")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries/{query_id}/download',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            size_kb = len(response.content) / 1024
            record_result(f"GET /queries/{query_id}/download", True, f"Downloaded {size_kb:.2f} KB")
            return True
        elif response.status_code == 404:
            record_result(f"GET /queries/{query_id}/download", False, "Query folder not found", response)
            return False
        else:
            record_result(f"GET /queries/{query_id}/download", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result(f"GET /queries/{query_id}/download", False, f"Error: {str(e)}")
        return False


# ============================================================================
# FILE TESTS
# ============================================================================

def test_get_latest_containers():
    """Test 16: Get Latest Containers"""
    print_header("Test 16: Get Latest Containers", "-")
    
    if not USER_TOKEN:
        skip_test("GET /files/containers", "No user token available")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/containers',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            size_kb = len(response.content) / 1024
            record_result("GET /files/containers", True, f"Downloaded {size_kb:.2f} KB")
            return True
        elif response.status_code == 404:
            record_result("GET /files/containers", False, "File not found (no queries run yet)", response)
            return False
        else:
            record_result("GET /files/containers", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("GET /files/containers", False, f"Error: {str(e)}")
        return False


def test_get_latest_appointments():
    """Test 17: Get Latest Appointments"""
    print_header("Test 17: Get Latest Appointments", "-")
    
    if not USER_TOKEN:
        skip_test("GET /files/appointments", "No user token available")
        return False
    
    try:
        response = requests.get(
            f'{BASE_URL}/files/appointments',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            size_kb = len(response.content) / 1024
            record_result("GET /files/appointments", True, f"Downloaded {size_kb:.2f} KB")
            return True
        elif response.status_code == 404:
            record_result("GET /files/appointments", False, "File not found (no queries run yet)", response)
            return False
        else:
            record_result("GET /files/appointments", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result("GET /files/appointments", False, f"Error: {str(e)}")
        return False


def test_get_query_files(query_id):
    """Test 18-21: Get Query-Specific Files"""
    print_header("Test 18-21: Get Query-Specific Files", "-")
    
    if not USER_TOKEN:
        skip_test("GET /files/queries/{id}/*", "No user token available")
        return
    
    if not query_id:
        skip_test("GET /files/queries/{id}/*", "No query ID available")
        return
    
    # Test 18: All containers
    try:
        response = requests.get(
            f'{BASE_URL}/files/queries/{query_id}/all-containers',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result(f"GET /files/queries/{query_id}/all-containers", True, "File downloaded", response)
        elif response.status_code == 404:
            record_result(f"GET /files/queries/{query_id}/all-containers", False, "File not found", response)
        else:
            record_result(f"GET /files/queries/{query_id}/all-containers", False, f"Status: {response.status_code}", response)
    except Exception as e:
        record_result(f"GET /files/queries/{query_id}/all-containers", False, f"Error: {str(e)}")
    
    # Test 19: Filtered containers
    try:
        response = requests.get(
            f'{BASE_URL}/files/queries/{query_id}/filtered-containers',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result(f"GET /files/queries/{query_id}/filtered-containers", True, "File downloaded", response)
        elif response.status_code == 404:
            record_result(f"GET /files/queries/{query_id}/filtered-containers", False, "File not found", response)
        else:
            record_result(f"GET /files/queries/{query_id}/filtered-containers", False, f"Status: {response.status_code}", response)
    except Exception as e:
        record_result(f"GET /files/queries/{query_id}/filtered-containers", False, f"Error: {str(e)}")
    
    # Test 20: All appointments
    try:
        response = requests.get(
            f'{BASE_URL}/files/queries/{query_id}/all-appointments',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result(f"GET /files/queries/{query_id}/all-appointments", True, "File downloaded", response)
        elif response.status_code == 404:
            record_result(f"GET /files/queries/{query_id}/all-appointments", False, "File not found", response)
        else:
            record_result(f"GET /files/queries/{query_id}/all-appointments", False, f"Status: {response.status_code}", response)
    except Exception as e:
        record_result(f"GET /files/queries/{query_id}/all-appointments", False, f"Error: {str(e)}")


def test_delete_query(query_id):
    """Test 22: Delete Query (Cleanup)"""
    print_header("Test 22: Delete Query", "-")
    
    if not USER_TOKEN:
        skip_test("DELETE /queries/{id}", "No user token available")
        return False
    
    if not query_id:
        skip_test("DELETE /queries/{id}", "No query ID available")
        return False
    
    try:
        response = requests.delete(
            f'{BASE_URL}/queries/{query_id}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result(f"DELETE /queries/{query_id}", True, "Query deleted", response)
            return True
        else:
            record_result(f"DELETE /queries/{query_id}", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result(f"DELETE /queries/{query_id}", False, f"Error: {str(e)}")
        return False


def test_delete_test_user(user_id):
    """Test 23: Delete Test User (Cleanup)"""
    print_header("Test 23: Delete Test User (Cleanup)", "-")
    
    if not user_id:
        skip_test("DELETE /admin/users/{id}/flush", "No user ID available")
        return False
    
    try:
        response = requests.delete(
            f'{BASE_URL}/admin/users/{user_id}/flush',
            headers={'X-Admin-Key': ADMIN_KEY},
            timeout=2400
        )
        
        if response.status_code == 200:
            record_result(f"DELETE /admin/users/{user_id}/flush", True, "User deleted", response)
            return True
        else:
            record_result(f"DELETE /admin/users/{user_id}/flush", False, f"Status: {response.status_code}", response)
            return False
            
    except Exception as e:
        record_result(f"DELETE /admin/users/{user_id}/flush", False, f"Error: {str(e)}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']
    skipped = test_results['skipped']
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests:   {total}")
    print(f"[PASS] Passed:      {passed}")
    print(f"[FAIL] Failed:      {failed}")
    print(f"[SKIP] Skipped:     {skipped}")
    print(f"Pass Rate:     {pass_rate:.1f}%")
    
    # Save detailed results
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n[INFO] Detailed results saved to: {results_file}")


def main():
    print_header("E-MODAL MANAGEMENT SYSTEM - COMPREHENSIVE TEST SUITE")
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Key: {ADMIN_KEY[:20]}...")
    print(f"User Token: {USER_TOKEN[:20] if USER_TOKEN else 'Not loaded'}...")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # System Tests
    server_running = test_health_check()
    if not server_running:
        print("\n[ERROR] Server is not running! Please start it first:")
        print("   python app.py")
        return
    
    test_root_endpoint()
    
    # Admin Tests
    users = test_list_users()
    user = test_get_user(USER_ID)
    
    # Create test user for testing
    test_user = test_create_test_user()
    test_user_id = test_user['id'] if test_user else None
    
    if test_user_id:
        test_update_credentials(test_user_id)
    
    # Schedule Tests
    test_get_schedule()
    test_update_schedule()
    test_pause_schedule()
    test_resume_schedule()
    
    # Query Tests
    triggered_query_id = test_trigger_query()
    queries = test_list_queries()
    test_list_queries_filtered()
    
    # Use existing query ID if available
    query_id_to_test = triggered_query_id
    if not query_id_to_test and queries:
        query_id_to_test = queries[0]['query_id']
    
    if query_id_to_test:
        test_get_query(query_id_to_test)
        test_download_query(query_id_to_test)
    
    # File Tests
    test_get_latest_containers()
    test_get_latest_appointments()
    
    if query_id_to_test:
        test_get_query_files(query_id_to_test)
    
    # Cleanup Tests
    if triggered_query_id:
        print("\n[INFO] Waiting 5 seconds before cleanup...")
        time.sleep(5)
        test_delete_query(triggered_query_id)
    
    if test_user_id:
        test_delete_test_user(test_user_id)
    
    # Print Summary
    print_summary()
    
    print_header("TESTING COMPLETE")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()

