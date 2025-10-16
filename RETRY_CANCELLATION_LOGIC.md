# Retry Cancellation Logic - Smart Query Management

## Problem

When a query encounters a 401 UNAUTHORIZED error:
- System waits 10 minutes before retrying
- If user manually triggers a new query during this wait
- The old query would still retry after 10 minutes
- This wastes resources and creates confusion

**Scenario:**
```
Query A starts → 401 error → Waiting 10 minutes...
  (5 minutes pass)
User triggers Query B manually
  (Query B starts fresh session successfully)
  (5 more minutes pass)
Query A wakes up and retries → Wastes time! ❌
```

## Solution

**Smart cancellation**: If a newer query is triggered during the wait period, the old query's retry is automatically cancelled.

**New Scenario:**
```
Query A starts → 401 error → Waiting 10 minutes...
  (5 minutes pass)
User triggers Query B manually
  (Query B creates session successfully)
Query A detects newer query → Cancels retry → Stops ✅
```

---

## How It Works

### 1. During 10-Minute Wait

Every minute (60 seconds), the system checks:
```python
if current_query_id and self._check_newer_query_exists(user.id, current_query_id):
    print("Newer query detected - cancelling automatic retry")
    return None  # Cancel and exit
```

### 2. Query ID Comparison

Query IDs have format: `q_{user_id}_{timestamp}`

Example:
- Query A: `q_1_1759809697` (timestamp: 1759809697)
- Query B: `q_1_1759809800` (timestamp: 1759809800)

System extracts timestamps and compares:
```python
current_timestamp = int('q_1_1759809697'.split('_')[-1])  # 1759809697
newer_timestamp = int('q_1_1759809800'.split('_')[-1])    # 1759809800

if newer_timestamp > current_timestamp:
    # Newer query exists - cancel retry
    return None
```

### 3. Cancellation Points

The system checks for newer queries at these points:
- **Every minute** during the 10-minute wait
- **Before each retry attempt**
- **In both `_ensure_session()` and `_recover_session()`**

---

## Implementation Details

### New Method: `_check_newer_query_exists()`

```python
def _check_newer_query_exists(self, user_id, current_query_id):
    """
    Check if a newer query exists for the user
    
    Returns:
        True if newer query found, False otherwise
    """
    # Extract timestamp from current query
    current_timestamp = int(current_query_id.split('_')[-1])
    
    # Get all queries for this user
    queries = Query.query.filter(
        Query.user_id == user_id,
        Query.query_id != current_query_id
    ).all()
    
    # Check if any have newer timestamp
    for query in queries:
        query_timestamp = int(query.query_id.split('_')[-1])
        if query_timestamp > current_timestamp:
            return True  # Newer query exists!
    
    return False  # No newer queries
```

### Updated Methods

Both methods now accept `current_query_id` parameter:

1. **`_ensure_session(user, max_retries=3, retry_delay_minutes=10, current_query_id=None)`**
2. **`_recover_session(user, max_retries=3, retry_delay_minutes=10, current_query_id=None)`**

### Updated Calls

All calls to these methods now pass `current_query_id`:

```python
# In execute_query()
session_id = self._ensure_session(user, current_query_id=query_id)

# In _execute_query_steps() for get_containers retry
session_id = self._recover_session(user, current_query_id=query.query_id)

# In _execute_query_steps() for get_appointments retry
session_id = self._recover_session(user, current_query_id=query.query_id)

# In _check_containers_with_bulk_info() for individual container retries
new_session_id = self._recover_session(user, current_query_id=current_query_id)

# In routes/queries.py background thread
session_id = query_service._ensure_session(user_obj, current_query_id=query_id)
```

---

## Console Output

### When Cancellation Occurs:
```
[WARNING] 401 UNAUTHORIZED - Session creation failed
[INFO] This is likely a temporary issue with 2captcha or E-Modal
[INFO] Waiting 10 minutes before retry 2/3...
[INFO] (Retry will be cancelled if a new query is manually triggered)
[INFO] Waiting... 10 minutes remaining
[INFO] Waiting... 9 minutes remaining
[INFO] Waiting... 8 minutes remaining
[INFO] Waiting... 7 minutes remaining
[INFO] Waiting... 6 minutes remaining

[INFO] Newer query detected - cancelling automatic retry
[INFO] The new query will handle session creation
```

### When No Cancellation (Retry Continues):
```
[WARNING] 401 UNAUTHORIZED - Session creation failed
[INFO] Waiting 10 minutes before retry 2/3...
[INFO] (Retry will be cancelled if a new query is manually triggered)
[INFO] Waiting... 10 minutes remaining
...
[INFO] Waiting... 1 minutes remaining
[INFO] Retrying session creation now...
[INFO] Session created successfully: session_1759808540_...
```

---

## Example Scenarios

### Scenario 1: User Triggers New Query During Wait

```
10:00 AM - Query A triggered → 401 error
10:00 AM - Query A starts 10-minute wait
10:05 AM - User manually triggers Query B
10:05 AM - Query B creates session successfully
10:05 AM - Query A detects Query B → Cancels retry
10:05 AM - Query A marked as failed: "Retry cancelled - newer query was manually triggered"
```

**Result**: Only Query B continues. No wasted effort.

### Scenario 2: No Manual Trigger During Wait

```
10:00 AM - Query A triggered → 401 error
10:00 AM - Query A starts 10-minute wait
10:10 AM - No new queries detected
10:10 AM - Query A retries session creation
10:10 AM - Session created successfully ✅
10:10 AM - Query A continues normally
```

**Result**: Automatic retry succeeds after wait.

### Scenario 3: Multiple Retries with Manual Trigger

```
10:00 AM - Query A triggered → 401 error (attempt 1)
10:00 AM - Query A starts wait #1 (10 minutes)
10:10 AM - Query A retries → 401 error (attempt 2)
10:10 AM - Query A starts wait #2 (10 minutes)
10:15 AM - User triggers Query B
10:15 AM - Query B creates session successfully
10:15 AM - Query A detects Query B → Cancels retry
```

**Result**: Query A cancelled after 15 minutes total. Query B succeeds.

---

## Benefits

### ✅ Resource Efficiency
- No wasted retries if user manually intervenes
- Cancelled queries free up resources immediately
- Only one active query per user

### ✅ User Experience
- Manual trigger supersedes automatic retry
- User has full control
- Clear feedback on what's happening

### ✅ Database Cleanliness
- Old queries marked as failed with clear reason
- Easy to identify cancelled vs truly failed queries
- Proper audit trail

---

## Query Status Messages

### Cancelled Query:
```json
{
  "query_id": "q_1_1759809697",
  "status": "failed",
  "error_message": "Retry cancelled - newer query was manually triggered",
  "completed_at": "2025-10-11T10:05:00"
}
```

### Successful After Retry:
```json
{
  "query_id": "q_1_1759809697",
  "status": "completed",
  "summary_stats": {...},
  "completed_at": "2025-10-11T10:30:00"
}
```

### Failed After All Retries:
```json
{
  "query_id": "q_1_1759809697",
  "status": "failed",
  "error_message": "Failed to create E-Modal session after 3 attempts: 401 UNAUTHORIZED",
  "completed_at": "2025-10-11T10:30:00"
}
```

---

## Technical Details

### Thread Safety
- Database queries are thread-safe (SQLAlchemy handles locking)
- Each query runs in its own thread
- No race conditions between cancellation check and query creation

### Performance
- Cancellation check runs once per minute (low overhead)
- Simple timestamp comparison (very fast)
- No blocking between queries

### Edge Cases Handled

1. **Query ID Parse Error**: If timestamp can't be extracted, retry continues (safe fallback)
2. **Database Error**: If check fails, retry continues (don't break retry logic)
3. **No Current Query ID**: If `current_query_id` is None, cancellation is skipped
4. **Simultaneous Triggers**: Newest timestamp always wins

---

## Configuration

### Default Settings:
```python
max_retries = 3                # 3 total attempts
retry_delay_minutes = 10       # 10 minutes between retries
```

### Check Frequency:
```python
# Checks every 60 seconds during wait
time.sleep(60)
```

---

## Future Enhancements

1. **User Notification**: Send webhook/email when retry is cancelled
2. **Retry Queue**: Maintain queue of pending retries per user
3. **Priority System**: Allow high-priority queries to cancel low-priority ones
4. **Custom Delays**: Different delays based on error type
5. **Exponential Backoff**: Increase wait time with each retry

---

## Summary

✅ Automatic retry cancellation when user triggers new query  
✅ Checks every minute during 10-minute wait  
✅ Compares query timestamps to find newer queries  
✅ Clear console feedback on cancellation  
✅ Prevents wasted resources  
✅ User manual triggers always supersede automatic retries  
✅ Proper error messages in database  

**Result**: Smart retry management that respects user actions and avoids unnecessary work! 🎯

---

**Updated**: 2025-10-11  
**Version**: 6.0


