# Postman Setup Guide

## Files Created:

1. **E-Modal_API.postman_collection.json** - API collection with all endpoints
2. **E-Modal_API.postman_environment.json** - Environment variables

---

## How to Import into Postman:

### Step 1: Import Collection

1. Open Postman
2. Click **Import** button (top left)
3. Select **E-Modal_API.postman_collection.json**
4. Click **Import**

### Step 2: Import Environment

1. Click the gear icon ⚙️ (top right, next to "No Environment")
2. Click **Import**
3. Select **E-Modal_API.postman_environment.json**
4. Click **Import**

### Step 3: Activate Environment

1. Click the dropdown next to the gear icon ⚙️
2. Select **E-Modal API - Local**

---

## Collection Structure:

### 📁 Admin Endpoints (5 endpoints)
- **POST** Create User
- **GET** List Users
- **GET** Get User
- **PUT** Update User Credentials
- **DELETE** Delete User

### 📁 Queries Endpoints (3 endpoints)
- **POST** Trigger Query
- **GET** Get Query Status
- **GET** List All Queries

### 📁 Files Endpoints (6 endpoints)
- **GET** Get Latest Containers File
- **GET** Get Latest Appointments File
- **GET** Get Specific Query Containers
- **GET** Get Specific Query Appointments
- **POST** Update Containers File
- **POST** Update Appointments File

### 📁 Schedule Endpoints (3 endpoints)
- **GET** Get Schedule Status
- **POST** Enable Schedule
- **POST** Disable Schedule

### 📁 System Endpoints (3 endpoints)
- **GET** Health Check
- **GET** Root Endpoint
- **GET** List Routes

---

## Environment Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | http://localhost:5000 | Flask API URL |
| `user_token` | TWDy1cZoqK9h | User authentication token |
| `admin_key` | 6G8NlWa8W38MYTis | Admin secret key |
| `user_id` | 1 | User ID for testing |
| `query_id` | q_1_1759809010 | Query ID for testing |
| `emodal_api_url` | http://localhost:5010 | Internal E-Modal API URL |
| `emodal_username` | jfernandez | E-Modal username |
| `emodal_password` | taffie | E-Modal password (secret) |
| `emodal_captcha_key` | 7bf85bb6f37c9799543a2a463aab2b4f | Captcha API key (secret) |

---

## How to Use:

### 1. **Test System Health**
Run: **System > Health Check**
- Should return status: healthy

### 2. **Test User Management**
Run: **Admin > List Users**
- Should return list of users

### 3. **Trigger a Query**
Run: **Queries > Trigger Query**
- Should return query_id
- Copy the query_id from response

### 4. **Check Query Status**
1. Update `query_id` variable with the query_id from step 3
2. Run: **Queries > Get Query Status**
3. Check the status (pending/running/completed/failed)

### 5. **Get Files**
After query completes:
- Run: **Files > Get Latest Containers File**
- Run: **Files > Get Latest Appointments File**

### 6. **Manage Schedule**
- Run: **Schedule > Get Schedule Status**
- Run: **Schedule > Enable Schedule** (to auto-run hourly)
- Run: **Schedule > Disable Schedule** (to stop auto-run)

---

## Quick Test Workflow:

```
1. System > Health Check              ✓ Check server is running
2. Admin > List Users                 ✓ Verify user exists
3. Queries > Trigger Query            ✓ Start new query
4. Queries > Get Query Status         ✓ Check progress
5. Files > Get Latest Containers      ✓ Download results
6. Files > Get Latest Appointments    ✓ Download results
```

---

## Updating Variables:

### To update the user token:
1. Get token from database: `python get_token.py` (if you still have this script)
2. Or manually: Open SQLite database and get token from users table
3. Update `user_token` variable in environment

### To test different query:
1. Trigger a new query
2. Copy the `query_id` from response
3. Update `query_id` variable in environment
4. Run "Get Query Status"

---

## Tips:

- All requests use **localhost:5000** by default
- Update `base_url` to use a different server
- Admin endpoints require `X-Admin-Key` header
- User endpoints require `Authorization: Bearer <token>` header
- Variables can be changed in the Environment tab

---

## Troubleshooting:

### "Connection refused" error
- Make sure Flask server is running: `python app.py`
- Check the server is on localhost:5000

### "Unauthorized" error
- Check `user_token` is correct
- Check `admin_key` matches your .env file

### "Query not found" error
- Update `query_id` variable with a valid query ID
- Run "List All Queries" to see available queries

---

**Ready to test all endpoints in Postman!** 🚀

