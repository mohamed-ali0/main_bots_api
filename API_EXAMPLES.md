# API Usage Examples

This document provides practical examples for using the E-Modal Management System API.

## Table of Contents

1. [Admin Operations](#admin-operations)
2. [User Operations](#user-operations)
3. [Query Management](#query-management)
4. [File Access](#file-access)
5. [Schedule Management](#schedule-management)

---

## Admin Operations

### 1. Create a New User

```python
import requests

admin_key = "your-admin-key-here"

response = requests.post(
    'http://localhost:5000/admin/users',
    headers={'X-Admin-Key': admin_key},
    json={
        'name': 'John Fernandez',
        'username': 'jfernandez',
        'password': 'secure_password_123',
        'emodal_username': 'jfernandez',
        'emodal_password': 'taffie',
        'emodal_captcha_key': '7bf85bb6f37c9799543a2a463aab2b4f'
    }
)

if response.status_code == 201:
    user_data = response.json()
    print(f"User created successfully!")
    print(f"User ID: {user_data['user']['id']}")
    print(f"Token: {user_data['user']['token']}")
    # Save this token!
else:
    print(f"Error: {response.json()}")
```

### 2. List All Users

```python
import requests

admin_key = "your-admin-key-here"

response = requests.get(
    'http://localhost:5000/admin/users',
    headers={'X-Admin-Key': admin_key}
)

users = response.json()['users']
print(f"Total users: {len(users)}")
for user in users:
    print(f"- {user['username']} ({user['name']}) - {user['query_count']} queries")
```

### 3. Get User Details

```python
import requests

admin_key = "your-admin-key-here"
user_id = 1

response = requests.get(
    f'http://localhost:5000/admin/users/{user_id}',
    headers={'X-Admin-Key': admin_key}
)

user = response.json()['user']
print(f"Username: {user['username']}")
print(f"Token: {user['token']}")
print(f"Schedule Enabled: {user['schedule_enabled']}")
print(f"Query Count: {user['query_count']}")
```

### 4. Update User Credentials

```python
import requests

admin_key = "your-admin-key-here"
user_id = 1

response = requests.put(
    f'http://localhost:5000/admin/users/{user_id}/credentials',
    headers={'X-Admin-Key': admin_key},
    json={
        'platform': 'emodal',
        'credentials': {
            'username': 'new_username',
            'password': 'new_password',
            'captcha_api_key': 'new_api_key'
        }
    }
)

print(response.json())
```

### 5. Delete User

```python
import requests

admin_key = "your-admin-key-here"
user_id = 1

# Warning: This deletes all user data!
response = requests.delete(
    f'http://localhost:5000/admin/users/{user_id}/flush',
    headers={'X-Admin-Key': admin_key}
)

print(response.json())
```

---

## User Operations

### Authentication

All user operations require a Bearer token:

```python
import requests

token = "your-user-token-here"
headers = {'Authorization': f'Bearer {token}'}

# Use this headers dict in all user requests
response = requests.get('http://localhost:5000/queries', headers=headers)
```

---

## Query Management

### 1. Trigger a Manual Query

```python
import requests

token = "your-user-token-here"

response = requests.post(
    'http://localhost:5000/queries/trigger',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 202:
    query_data = response.json()
    query_id = query_data['query_id']
    print(f"Query started: {query_id}")
else:
    print(f"Error: {response.json()}")
```

### 2. List All Queries

```python
import requests

token = "your-user-token-here"

# List all queries
response = requests.get(
    'http://localhost:5000/queries',
    headers={'Authorization': f'Bearer {token}'}
)

queries = response.json()['queries']
print(f"Total queries: {response.json()['total']}")

for query in queries:
    print(f"\nQuery: {query['query_id']}")
    print(f"Status: {query['status']}")
    print(f"Started: {query['started_at']}")
    if query['summary_stats']:
        stats = query['summary_stats']
        print(f"Containers: {stats.get('total_containers', 0)}")
        print(f"Appointments: {stats.get('total_appointments', 0)}")
```

### 3. Filter Queries by Status

```python
import requests

token = "your-user-token-here"

# Get only completed queries
response = requests.get(
    'http://localhost:5000/queries?status=completed&limit=10',
    headers={'Authorization': f'Bearer {token}'}
)

completed_queries = response.json()['queries']
print(f"Completed queries: {len(completed_queries)}")
```

### 4. Get Query Details

```python
import requests

token = "your-user-token-here"
query_id = "q_1_1728234567"

response = requests.get(
    f'http://localhost:5000/queries/{query_id}',
    headers={'Authorization': f'Bearer {token}'}
)

query = response.json()['query']
print(f"Query ID: {query['query_id']}")
print(f"Status: {query['status']}")
print(f"Summary: {query['summary_stats']}")
```

### 5. Download Query Results as ZIP

```python
import requests

token = "your-user-token-here"
query_id = "q_1_1728234567"

response = requests.get(
    f'http://localhost:5000/queries/{query_id}/download',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open(f'{query_id}.zip', 'wb') as f:
        f.write(response.content)
    print(f"Downloaded {query_id}.zip")
else:
    print(f"Error: {response.json()}")
```

### 6. Delete a Query

```python
import requests

token = "your-user-token-here"
query_id = "q_1_1728234567"

response = requests.delete(
    f'http://localhost:5000/queries/{query_id}',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.json())
```

---

## File Access

### 1. Download Latest Containers

```python
import requests

token = "your-user-token-here"

response = requests.get(
    'http://localhost:5000/files/containers',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open('all_containers.xlsx', 'wb') as f:
        f.write(response.content)
    print("Downloaded all_containers.xlsx")
else:
    print(f"Error: {response.json()}")
```

### 2. Download Latest Appointments

```python
import requests

token = "your-user-token-here"

response = requests.get(
    'http://localhost:5000/files/appointments',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open('all_appointments.xlsx', 'wb') as f:
        f.write(response.content)
    print("Downloaded all_appointments.xlsx")
```

### 3. Get Query-Specific Files

```python
import requests

token = "your-user-token-here"
query_id = "q_1_1728234567"

# Download filtered containers from specific query
response = requests.get(
    f'http://localhost:5000/files/queries/{query_id}/filtered-containers',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open(f'{query_id}_filtered.xlsx', 'wb') as f:
        f.write(response.content)
    print("Downloaded filtered containers")
```

### 4. Get Container Check Screenshot

```python
import requests

token = "your-user-token-here"
query_id = "q_1_1728234567"
filename = "MSCU5165756_1728234567.png"

response = requests.get(
    f'http://localhost:5000/files/queries/{query_id}/screenshots/{filename}',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded {filename}")
```

### 5. Get Container Check Response JSON

```python
import requests
import json

token = "your-user-token-here"
query_id = "q_1_1728234567"
filename = "MSCU5165756_1728234567.json"

response = requests.get(
    f'http://localhost:5000/files/queries/{query_id}/responses/{filename}',
    headers={'Authorization': f'Bearer {token}'}
)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
```

---

## Schedule Management

### 1. Get Current Schedule

```python
import requests

token = "your-user-token-here"

response = requests.get(
    'http://localhost:5000/schedule',
    headers={'Authorization': f'Bearer {token}'}
)

schedule = response.json()['schedule']
print(f"Enabled: {schedule['enabled']}")
print(f"Frequency: {schedule['frequency']} minutes")
```

### 2. Update Schedule Settings

```python
import requests

token = "your-user-token-here"

# Set to run every 2 hours
response = requests.put(
    'http://localhost:5000/schedule',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'enabled': True,
        'frequency': 120  # minutes
    }
)

schedule = response.json()['schedule']
print(f"Schedule updated: every {schedule['frequency']} minutes")
```

### 3. Pause Scheduled Queries

```python
import requests

token = "your-user-token-here"

response = requests.post(
    'http://localhost:5000/schedule/pause',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.json()['message'])
```

### 4. Resume Scheduled Queries

```python
import requests

token = "your-user-token-here"

response = requests.post(
    'http://localhost:5000/schedule/resume',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.json()['message'])
```

---

## Complete Workflow Example

```python
import requests
import time

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_KEY = 'your-admin-key-here'

# Step 1: Create a user (admin)
print("Creating user...")
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

user_token = response.json()['user']['token']
print(f"User created. Token: {user_token}")

# Step 2: Configure schedule
print("\nConfiguring schedule...")
requests.put(
    f'{BASE_URL}/schedule',
    headers={'Authorization': f'Bearer {user_token}'},
    json={'enabled': True, 'frequency': 60}
)
print("Schedule set to 60 minutes")

# Step 3: Trigger manual query
print("\nTriggering query...")
response = requests.post(
    f'{BASE_URL}/queries/trigger',
    headers={'Authorization': f'Bearer {user_token}'}
)
query_id = response.json()['query_id']
print(f"Query started: {query_id}")

# Step 4: Wait and check status
print("\nWaiting for query to complete...")
for i in range(10):
    time.sleep(5)
    response = requests.get(
        f'{BASE_URL}/queries/{query_id}',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    status = response.json()['query']['status']
    print(f"Status: {status}")
    
    if status in ['completed', 'failed']:
        break

# Step 5: Download results
if status == 'completed':
    print("\nDownloading results...")
    
    # Download containers
    response = requests.get(
        f'{BASE_URL}/files/queries/{query_id}/all-containers',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    with open('containers.xlsx', 'wb') as f:
        f.write(response.content)
    
    # Download filtered
    response = requests.get(
        f'{BASE_URL}/files/queries/{query_id}/filtered-containers',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    with open('filtered_containers.xlsx', 'wb') as f:
        f.write(response.content)
    
    print("Files downloaded successfully!")

print("\n✅ Workflow complete!")
```

---

## Error Handling

### Example with Error Handling

```python
import requests

def make_api_request(method, url, **kwargs):
    """Make API request with error handling"""
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.json()}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None

# Usage
token = "your-user-token-here"
result = make_api_request(
    'POST',
    'http://localhost:5000/queries/trigger',
    headers={'Authorization': f'Bearer {token}'}
)

if result:
    print(f"Query ID: {result['query_id']}")
else:
    print("Request failed")
```

---

## Tips and Best Practices

1. **Store Tokens Securely**: Never hardcode tokens in production code
2. **Handle Timeouts**: Long-running queries may take time
3. **Check Status Codes**: Always verify response status
4. **Use Error Handling**: Wrap API calls in try-except blocks
5. **Monitor Logs**: Check `logs/app.log` for issues
6. **Rate Limiting**: Consider implementing rate limiting for production
7. **Backup Data**: Regularly backup the `storage/` directory

---

## Integration Examples

### Django Integration

```python
# views.py
from django.http import JsonResponse
import requests

def trigger_emodal_query(request):
    token = request.user.emodal_token
    
    response = requests.post(
        'http://localhost:5000/queries/trigger',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    return JsonResponse(response.json())
```

### Celery Task

```python
# tasks.py
from celery import shared_task
import requests

@shared_task
def check_query_status(query_id, user_token):
    response = requests.get(
        f'http://localhost:5000/queries/{query_id}',
        headers={'Authorization': f'Bearer {user_token}'}
    )
    
    query_data = response.json()['query']
    
    if query_data['status'] == 'completed':
        # Process completed query
        process_query_results(query_data)
    elif query_data['status'] == 'failed':
        # Handle failure
        handle_query_failure(query_data)
```

---

For more information, see `README.md` and `QUICKSTART.md`.

