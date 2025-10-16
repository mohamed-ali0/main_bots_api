# 401 UNAUTHORIZED Retry Logic - Implementation

## Problem

When the E-Modal session creation fails with **401 UNAUTHORIZED** error:
- Usually caused by temporary issues with 2captcha service or E-Modal platform
- System would immediately fail the query
- User had to manually retry the entire query
- No automatic recovery mechanism

**Error Flow Before:**
```
Container request → 400 BAD REQUEST (expired session)
  ↓
Try to recover session → 401 UNAUTHORIZED
  ↓
Query fails immediately ❌
```

## Solution

Added **automatic retry logic with 10-minute delays** for 401 UNAUTHORIZED errors:
- System detects 401 errors during session creation
- Waits 10 minutes before retrying
- Attempts up to 3 times (configurable)
- Provides clear console feedback during wait

**Error Flow After:**
```
Container request → 400 BAD REQUEST (expired session)
  ↓
Try to recover session → 401 UNAUTHORIZED
  ↓
Wait 10 minutes... (with countdown)
  ↓
Retry session creation → Success! ✅
  ↓
Query continues normally
```

---

## Changes Made

### File: `services/query_service.py`

#### 1. Updated `_ensure_session()` Method

**New Parameters:**
- `max_retries=3`: Maximum retry attempts for 401 errors
- `retry_delay_minutes=10`: Minutes to wait between retries

**Behavior:**
- Detects 401 UNAUTHORIZED errors
- Waits 10 minutes before each retry
- Shows countdown in console
- Retries up to 3 times
- Fails only after all retries exhausted

#### 2. Updated `_recover_session()` Method

Same retry logic as `_ensure_session()`:
- 3 retry attempts with 10-minute delays
- Clear console feedback
- Countdown timer
- Automatic retry on 401 errors

---

## Console Output

### During Wait Period:
```
[WARNING] 401 UNAUTHORIZED - Session creation failed
[INFO] This is likely a temporary issue with 2captcha or E-Modal
[INFO] Waiting 10 minutes before retry 2/3...
[INFO] Waiting... 10 minutes remaining
[INFO] Waiting... 9 minutes remaining
[INFO] Waiting... 8 minutes remaining
...
[INFO] Waiting... 1 minutes remaining
[INFO] Retrying session creation now...
```

### After Successful Retry:
```
[INFO] Creating new E-Modal session for user jfernandez (attempt 2/3)
[INFO] Session created successfully: session_1759808540_-44251561...
```

### After All Retries Failed:
```
[ERROR] All 3 session creation attempts failed with 401 UNAUTHORIZED
Query failed: Failed to create E-Modal session after 3 attempts: 401 Client Error: UNAUTHORIZED
```

---

## Retry Logic Flow

```
Attempt 1: Try to create session
    ↓
  401 UNAUTHORIZED
    ↓
Wait 10 minutes
    ↓
Attempt 2: Try to create session
    ↓
  401 UNAUTHORIZED
    ↓
Wait 10 minutes
    ↓
Attempt 3: Try to create session
    ↓
  Success! ✅ or Final failure ❌
```

---

## Why 10 Minutes?

1. **2captcha service** may have temporary rate limits or queue delays
2. **E-Modal platform** may have temporary login restrictions
3. **Captcha generation** may take time to refresh
4. **Network issues** usually resolve within minutes
5. **Balance** between quick retry and avoiding rate limits

---

## Configuration

### Default Settings:
```python
max_retries = 3                # 3 attempts total
retry_delay_minutes = 10       # 10 minutes between retries
```

### To Customize:
Modify the method signatures in `services/query_service.py`:

```python
def _ensure_session(self, user, max_retries=5, retry_delay_minutes=15):
    # Will retry 5 times with 15-minute delays
```

---

## Error Types Handled

### Will Retry (401 errors):
- `401 Client Error: UNAUTHORIZED`
- `401 UNAUTHORIZED` in error message
- Authentication failures
- Captcha service issues

### Will NOT Retry (other errors):
- `400 BAD REQUEST` (different issue)
- `500 INTERNAL SERVER ERROR`
- `403 FORBIDDEN`
- Network connection errors
- Invalid credentials (permanent issue)

---

## Testing

### Test Scenario 1: Temporary 401 Error
```
1. Trigger query
2. System gets 401 on first attempt
3. Waits 10 minutes
4. Retries successfully
5. Query continues ✅
```

### Test Scenario 2: Persistent 401 Error
```
1. Trigger query
2. System gets 401 on attempt 1
3. Waits 10 minutes
4. Gets 401 on attempt 2
5. Waits 10 minutes
6. Gets 401 on attempt 3
7. Query fails after 30 minutes total ❌
```

### Test Scenario 3: Immediate Success
```
1. Trigger query
2. Session created on first attempt
3. No waiting, query continues immediately ✅
```

---

## Impact on Query Duration

### Best Case (No 401 errors):
- No additional time
- Query completes normally (30-40 minutes)

### With 1 Retry:
- +10 minutes wait time
- Query completes in ~40-50 minutes

### With 2 Retries:
- +20 minutes wait time
- Query completes in ~50-60 minutes

### With 3 Retries (all fail):
- +20 minutes wait time
- Query fails after ~30 minutes of retries

---

## Benefits

### ✅ Before (No Retry):
- ❌ Query fails immediately on 401
- ❌ User must manually retry
- ❌ Wastes processed data
- ❌ Poor user experience

### ✅ After (With Retry):
- ✅ Automatic recovery from temporary issues
- ✅ No manual intervention needed
- ✅ Preserves all processed data
- ✅ Much better user experience
- ✅ Clear feedback during wait
- ✅ Query continues seamlessly after recovery

---

## When to Use Manual Retry

Even with automatic retry, you may need manual intervention if:

1. **Invalid Credentials**: E-Modal username/password are wrong
2. **Invalid API Key**: 2captcha API key is incorrect
3. **Account Issues**: E-Modal account is locked/suspended
4. **Service Outage**: E-Modal platform is completely down

In these cases, the system will fail after 3 attempts (~30 minutes), and you'll need to:
- Check credentials in `user_cre_env.json`
- Verify 2captcha account has credits
- Check E-Modal account status
- Wait for service to come back online

---

## Monitoring

### Check Query Status:
```
GET /queries/{query_id}
```

### Query Status Values:
- `pending` - Query not started yet
- `in_progress` - Query running (may be in retry wait)
- `completed` - Query finished successfully
- `failed` - Query failed after all retries

### Check Error Message:
```json
{
  "query": {
    "status": "failed",
    "error_message": "Failed to create E-Modal session after 3 attempts: 401 UNAUTHORIZED"
  }
}
```

---

## Technical Details

### Thread Safety:
- Each retry sleeps for 60 seconds at a time (not blocking entire thread)
- Console updates every minute with countdown
- Database commits after successful session creation

### Memory:
- No additional memory overhead
- Session response stored only on success
- Failed attempts don't accumulate data

### Logging:
- All attempts logged with timestamps
- Wait periods logged
- Success/failure logged
- Full error messages preserved

---

## Summary

✅ System now automatically retries 401 UNAUTHORIZED errors  
✅ 3 attempts with 10-minute delays  
✅ Clear console feedback with countdown  
✅ Applies to both initial session creation and session recovery  
✅ Non-401 errors still fail immediately (no waiting)  
✅ Configurable retry count and delay  

**Result**: Much more robust query execution with automatic recovery from temporary 2captcha/E-Modal issues! 🎉

---

**Updated**: 2025-10-11  
**Version**: 5.0


