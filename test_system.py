import requests
import json
import time

BASE_URL = 'http://localhost:5000'
ADMIN_KEY = 'admin-dev-key-123'  # Update this with your actual admin key

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f'{BASE_URL}/health')
        print(f'Status Code: {response.status_code}')
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f'Error: {e}')
        return False


def test_create_user():
    """Test user creation"""
    print("\n=== Testing User Creation ===")
    try:
        response = requests.post(
            f'{BASE_URL}/admin/users',
            headers={'X-Admin-Key': ADMIN_KEY},
            json={
                'name': 'Test User',
                'username': 'testuser',
                'password': 'testpass123',
                'emodal_username': 'jfernandez',
                'emodal_password': 'taffie',
                'emodal_captcha_key': '7bf85bb6f37c9799543a2a463aab2b4f'
            }
        )
        print(f'Status Code: {response.status_code}')
        data = response.json()
        print(json.dumps(data, indent=2))
        if response.status_code in [200, 201] and data.get('success'):
            return data['user']['token']
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None


def test_list_users():
    """Test listing users"""
    print("\n=== Testing List Users ===")
    try:
        response = requests.get(
            f'{BASE_URL}/admin/users',
            headers={'X-Admin-Key': ADMIN_KEY}
        )
        print(f'Status Code: {response.status_code}')
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f'Error: {e}')


def test_trigger_query(token):
    """Test manual query trigger"""
    print("\n=== Testing Query Trigger ===")
    try:
        response = requests.post(
            f'{BASE_URL}/queries/trigger',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f'Status Code: {response.status_code}')
        data = response.json()
        print(json.dumps(data, indent=2))
        if response.status_code == 202 and data.get('success'):
            return data['query_id']
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None


def test_get_queries(token):
    """Test query listing"""
    print("\n=== Testing Get Queries ===")
    try:
        response = requests.get(
            f'{BASE_URL}/queries',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f'Status Code: {response.status_code}')
        data = response.json()
        print(json.dumps(data, indent=2))
        return data.get('queries', [])
    except Exception as e:
        print(f'Error: {e}')
        return []


def test_get_schedule(token):
    """Test get schedule settings"""
    print("\n=== Testing Get Schedule ===")
    try:
        response = requests.get(
            f'{BASE_URL}/schedule',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f'Status Code: {response.status_code}')
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f'Error: {e}')


def test_update_schedule(token):
    """Test update schedule settings"""
    print("\n=== Testing Update Schedule ===")
    try:
        response = requests.put(
            f'{BASE_URL}/schedule',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'enabled': True,
                'frequency': 120
            }
        )
        print(f'Status Code: {response.status_code}')
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f'Error: {e}')


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("E-Modal Management System - Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n⚠️  Server is not running or not healthy!")
        print("Please start the server with: python app.py")
        return
    
    # Test 2: List existing users
    test_list_users()
    
    # Test 3: Create user
    token = test_create_user()
    if not token:
        print("\n⚠️  User creation failed. User might already exist.")
        print("Testing with existing user...")
        # Try to use existing user for remaining tests
        # You'll need to manually provide a token here
        return
    
    # Test 4: Get schedule
    test_get_schedule(token)
    
    # Test 5: Update schedule
    test_update_schedule(token)
    
    # Test 6: Trigger query
    query_id = test_trigger_query(token)
    
    # Test 7: Wait a bit then check queries
    if query_id:
        print(f"\n⏳ Waiting 5 seconds for query to process...")
        time.sleep(5)
        test_get_queries(token)
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("=" * 60)
    print(f"\n💡 Your user token: {token}")
    print("Save this token for API requests!")


if __name__ == '__main__':
    run_all_tests()

