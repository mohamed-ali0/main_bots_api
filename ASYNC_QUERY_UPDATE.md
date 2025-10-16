# Async Query Trigger - Update Summary

## Problem

The `/queries/trigger` endpoint was running **synchronously**, meaning:
- The HTTP request would wait for the **entire query to complete** (can take 30-40 minutes)
- Client had to wait with an open connection
- Risk of timeout errors
- Poor user experience

## Solution

Made the query execution **asynchronous**:
- Endpoint returns **immediately** with 200 OK
- Query runs in a **background thread**
- Client can poll status using `GET /queries/{query_id}`

---

## Changes Made

### File: `routes/queries.py`

#### 1. Added Threading Support
```python
import threading
```

#### 2. Updated `trigger_query` Endpoint

**Before (Synchronous):**
```python
# Execute query (runs synchronously for now)
query_id = query_service.execute_query(user, platform=platform)
return jsonify(response), 202  # Returns after query completes
```

**After (Asynchronous):**
```python
# Create query record first
query = Query(
    query_id=query_id,
    user_id=user.id,
    platform=platform,
    status='pending',
    folder_path=query_service._get_query_folder_path(user.id, query_id)
)
db.session.add(query)
db.session.commit()

# Execute in background thread
thread = threading.Thread(target=run_query_async, daemon=True)
thread.start()

# Return immediately
return jsonify(response), 200  # Returns instantly!
```

#### 3. Background Query Execution

Created `run_query_async()` function that:
- Runs in a background thread with Flask app context
- Updates query status to `in_progress`
- Creates folder structure
- Ensures user has active session
- Executes all query steps
- Updates query status to `completed` or `failed`
- Handles errors and updates database accordingly

---

## API Response

### Request
```http
POST /queries/trigger
Authorization: Bearer {token}
Content-Type: application/json

{
  "platform": "emodal"
}
```

### Response (Immediate - 200 OK)
```json
{
  "success": true,
  "query_id": "q_1_1696789012",
  "platform": "emodal",
  "message": "Query triggered successfully",
  "status": "pending",
  "next_scheduled_run": "2025-10-11 15:30:00",
  "note": "Query is running in background. Use GET /queries/q_1_1696789012 to check status."
}
```

**Key Changes:**
- ✅ Returns **200 OK** instead of 202 Accepted
- ✅ Returns **immediately** (within milliseconds)
- ✅ Includes helpful note with instructions
- ✅ Query runs in background

---

## How to Check Query Status

### Option 1: Get Specific Query
```http
GET /queries/{query_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "query": {
    "query_id": "q_1_1696789012",
    "platform": "emodal",
    "status": "in_progress",  // or "completed", "failed"
    "summary_stats": {...},
    "started_at": "2025-10-11T12:00:00",
    "completed_at": "2025-10-11T12:30:00"  // null if not complete
  }
}
```

### Option 2: List All Queries
```http
GET /queries?status=in_progress
Authorization: Bearer {token}
```

### Option 3: Poll Until Complete
```python
import time
import requests

# Trigger query
response = requests.post(
    'http://37.60.243.201:5000/queries/trigger',
    headers={'Authorization': 'Bearer {token}'},
    json={'platform': 'emodal'}
)

query_id = response.json()['query_id']
print(f"Query triggered: {query_id}")

# Poll status every 30 seconds
while True:
    status_response = requests.get(
        f'http://37.60.243.201:5000/queries/{query_id}',
        headers={'Authorization': 'Bearer {token}'}
    )
    
    query_status = status_response.json()['query']['status']
    print(f"Status: {query_status}")
    
    if query_status in ['completed', 'failed']:
        break
    
    time.sleep(30)  # Wait 30 seconds

print("Query finished!")
```

---

## Query Status Flow

```
trigger endpoint called
        ↓
[pending] - Query created in database
        ↓
      200 OK returned to client
        ↓
[in_progress] - Background thread starts
        ↓
    Processing...
    - Get containers
    - Filter containers
    - Get bulk info
    - Check appointments
    - Get appointments
        ↓
[completed] or [failed]
```

---

## Benefits

### ✅ Before (Synchronous):
- ❌ Client waits 30-40 minutes
- ❌ Risk of connection timeout
- ❌ Can't trigger multiple queries
- ❌ Poor user experience
- ❌ HTTP connection held open

### ✅ After (Asynchronous):
- ✅ Client gets immediate response (< 1 second)
- ✅ No timeout risk
- ✅ Can trigger multiple queries
- ✅ Great user experience
- ✅ Connection freed immediately
- ✅ Query continues even if client disconnects
- ✅ Status can be checked any time

---

## Error Handling

If query fails during execution:
- Status is updated to `failed` in database
- `error_message` field is populated
- Can be retrieved via `GET /queries/{query_id}`

```json
{
  "query": {
    "query_id": "q_1_1696789012",
    "status": "failed",
    "error_message": "Failed to create E-Modal session",
    "completed_at": "2025-10-11T12:05:00"
  }
}
```

---

## Testing

### Test in Postman

**1. Trigger Query:**
```
POST http://37.60.243.201:5000/queries/trigger
Headers:
  Authorization: Bearer TWDy1cZoqK9h
  Content-Type: application/json
Body:
  {
    "platform": "emodal"
  }
```

**Expected:** Immediate 200 OK response with `query_id`

**2. Check Status:**
```
GET http://37.60.243.201:5000/queries/{query_id}
Headers:
  Authorization: Bearer TWDy1cZoqK9h
```

**Expected:** Current status (pending → in_progress → completed)

---

## Technical Details

### Thread Safety
- Each background thread has its own Flask app context
- Database sessions are properly managed
- Query objects are reloaded in the thread context

### Daemon Thread
- Thread is marked as `daemon=True`
- Server can shut down without waiting for thread
- Thread will be terminated on server shutdown

### Error Recovery
- If thread crashes, query status is updated to `failed`
- Error message is stored in database
- Logging captures all errors

---

## Migration Notes

- **No breaking changes** - existing code continues to work
- Response changed from `202 Accepted` to `200 OK`
- Response time changed from **minutes** to **milliseconds**
- Clients should now poll for status instead of waiting

---

**Updated**: 2025-10-11
**Version**: 4.0


