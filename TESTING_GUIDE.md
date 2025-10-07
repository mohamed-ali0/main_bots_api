# Testing Guide - E-Modal Management System

This guide explains how to add a user and run comprehensive tests.

## 📋 Overview

Two new scripts have been created:
1. **`add_user.py`** - Adds user with E-Modal credentials and session ID
2. **`test_all_endpoints.py`** - Comprehensive test suite for all 22 endpoints

## 🚀 Quick Start

### Step 1: Start the Server

```bash
python app.py
```

### Step 2: Add User

```bash
python add_user.py
```

This script will:
- ✅ Check if server is running
- ✅ Create user with credentials:
  - Username: `jfernandez`
  - Password: `taffie`
  - E-Modal username: `jfernandez`
  - E-Modal password: `taffie`
  - Captcha key: `7bf85bb6f37c9799543a2a463aab2b4f`
- ✅ Save user info to `user_info.json`
- ✅ Create `set_session.py` helper script
- ✅ Provide instructions to set session ID

### Step 3: Set Session ID

The session ID `session_1759763507_-8222151154545660229` needs to be set in the database.

**Option 1: Using the helper script (Easiest)**
```bash
python set_session.py
```

**Option 2: Using Flask shell**
```bash
flask shell
>>> from models.user import User, db
>>> user = User.query.filter_by(username='jfernandez').first()
>>> user.session_id = 'session_1759763507_-8222151154545660229'
>>> db.session.commit()
>>> print('Session ID updated!')
>>> exit()
```

**Option 3: Using psql**
```bash
psql -U emodal_user -d emodal_db -c "UPDATE users SET session_id = 'session_1759763507_-8222151154545660229' WHERE username = 'jfernandez';"
```

### Step 4: Run Comprehensive Tests

```bash
python test_all_endpoints.py
```

## 📊 What Gets Tested

### System Endpoints (2 tests)
1. ✅ GET `/health` - Health check
2. ✅ GET `/` - Root endpoint

### Admin Endpoints (5 tests)
3. ✅ GET `/admin/users` - List all users
4. ✅ GET `/admin/users/{id}` - Get user details
5. ✅ POST `/admin/users` - Create test user
6. ✅ PUT `/admin/users/{id}/credentials` - Update credentials
7. ✅ DELETE `/admin/users/{id}/flush` - Delete test user (cleanup)

### Schedule Endpoints (4 tests)
8. ✅ GET `/schedule` - Get schedule settings
9. ✅ PUT `/schedule` - Update schedule settings
10. ✅ POST `/schedule/pause` - Pause schedule
11. ✅ POST `/schedule/resume` - Resume schedule

### Query Endpoints (6 tests)
12. ✅ POST `/queries/trigger` - Trigger manual query
13. ✅ GET `/queries` - List queries
14. ✅ GET `/queries?status=completed` - List filtered queries
15. ✅ GET `/queries/{id}` - Get query details
16. ✅ GET `/queries/{id}/download` - Download query ZIP
17. ✅ DELETE `/queries/{id}` - Delete query (cleanup)

### File Endpoints (5 tests)
18. ✅ GET `/files/containers` - Latest containers
19. ✅ GET `/files/appointments` - Latest appointments
20. ✅ GET `/files/queries/{id}/all-containers` - Query containers
21. ✅ GET `/files/queries/{id}/filtered-containers` - Filtered containers
22. ✅ GET `/files/queries/{id}/all-appointments` - Query appointments

**Total: 23 Tests covering all 22 API endpoints**

## 📄 Test Output

The test suite provides:
- ✅ Real-time progress with colored output
- ✅ Pass/Fail status for each test
- ✅ Detailed error messages
- ✅ Test summary with pass rate
- ✅ JSON file with detailed results

### Sample Output

```
================================================================================
  E-MODAL MANAGEMENT SYSTEM - COMPREHENSIVE TEST SUITE
================================================================================

Base URL: http://localhost:5000
Admin Key: admin-dev-key-123...
User Token: kN8x4mP9qR2t...
Start Time: 2025-10-06 20:30:00

================================================================================
  Test 1: Health Check
--------------------------------------------------------------------------------

✅ GET /health
   Status: healthy, Scheduler: running

================================================================================
  Test 2: Root Endpoint
--------------------------------------------------------------------------------

✅ GET /
   Service: E-Modal Management System

...

================================================================================
  TEST SUMMARY
================================================================================

Total Tests:   23
✅ Passed:      20
❌ Failed:      2
⏭️  Skipped:     1
Pass Rate:     87.0%

📄 Detailed results saved to: test_results_20251006_203045.json
```

## 🔍 Generated Files

After running the scripts, you'll have:

1. **`user_info.json`** - User credentials and token
   ```json
   {
     "user_id": 1,
     "username": "jfernandez",
     "token": "kN8x4mP9qR2t",
     "emodal_username": "jfernandez",
     "emodal_password": "taffie",
     "session_id": "session_1759763507_-8222151154545660229",
     "base_url": "http://localhost:5000"
   }
   ```

2. **`set_session.py`** - Helper script to set session ID
   ```python
   # Automatically sets session ID for the user
   ```

3. **`test_results_YYYYMMDD_HHMMSS.json`** - Detailed test results
   ```json
   {
     "passed": 20,
     "failed": 2,
     "skipped": 1,
     "total": 23,
     "details": [...]
   }
   ```

## ⚠️ Important Notes

### Test Query Execution
- The test that triggers a query (Test 12) will start a real E-Modal query
- This query may take several minutes to complete
- The test will continue without waiting for completion
- Check query status later with: `GET /queries`

### File Download Tests
- File download tests (Tests 18-22) may fail if no queries have completed yet
- This is expected on first run
- Run tests again after a query completes to see these tests pass

### Session ID Requirement
- The session ID must be set for queries to work
- Without it, queries will fail when trying to communicate with E-Modal
- Make sure to run one of the session ID setting methods before testing queries

## 🔧 Customizing Tests

### Change Admin Key
Edit `test_all_endpoints.py`:
```python
ADMIN_KEY = 'your-admin-key-here'
```

### Change Base URL
Edit both scripts:
```python
BASE_URL = 'http://your-server:5000'
```

### Skip Certain Tests
Comment out the test function calls in `main()`:
```python
# test_trigger_query()  # Skip query trigger test
```

## 🐛 Troubleshooting

### Server Not Running
```
❌ GET /health
   Error: Connection refused
```
**Solution**: Start the server with `python app.py`

### Invalid Admin Key
```
❌ GET /admin/users
   Status: 403
```
**Solution**: Update `ADMIN_KEY` in the test script

### No User Token
```
⏭️  GET /schedule
   SKIPPED: No user token available
```
**Solution**: Run `add_user.py` first to create user and get token

### Query Tests Fail
```
❌ POST /queries/trigger
   Error: Failed to create E-Modal session
```
**Solution**: 
1. Make sure session ID is set
2. Verify E-Modal API is running
3. Check credentials in `user_cre_env.json`

### File Not Found
```
❌ GET /files/containers
   File not found (no queries run yet)
```
**Solution**: Run at least one query first (`POST /queries/trigger`)

## 📊 Understanding Test Results

### Pass ✅
- Endpoint returned expected status code
- Response contains expected data
- Operation completed successfully

### Fail ❌
- Endpoint returned error status code
- Response missing expected data
- Exception occurred during request

### Skip ⏭️
- Required data not available (e.g., no token, no query ID)
- Test dependencies not met
- Intentionally skipped

## 🎯 Best Practices

1. **Run add_user.py first** to set up test user
2. **Set session ID** before testing queries
3. **Review test output** for any failures
4. **Check detailed results** in the JSON file
5. **Run tests multiple times** to verify consistency
6. **Monitor server logs** (`logs/app.log`) during tests

## 📈 Continuous Testing

### Automated Testing
Add to cron or task scheduler:
```bash
# Run tests daily at 2 AM
0 2 * * * cd /path/to/app && python test_all_endpoints.py
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run API Tests
  run: |
    python app.py &
    sleep 5
    python add_user.py
    python set_session.py
    python test_all_endpoints.py
```

## 🔗 Related Documentation

- **API_EXAMPLES.md** - Detailed API usage examples
- **README.md** - Complete system documentation
- **QUICKSTART.md** - Quick setup guide

## 💡 Tips

1. Keep `user_info.json` secure - it contains authentication tokens
2. Review failed tests to identify system issues
3. Use test results for monitoring system health
4. Run tests after deployments to verify functionality
5. Save test result JSON files for historical comparison

---

**Happy Testing! 🧪**

For questions or issues, check the main README.md or server logs.

