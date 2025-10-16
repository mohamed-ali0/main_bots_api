# 📮 Postman Complete Setup Guide

## 📁 Files Generated

1. **E-Modal_API_Complete.postman_collection.json** - Complete API collection with all endpoints
2. **E-Modal_API_Complete.postman_environment.json** - Pre-configured environment with all credentials

---

## 🚀 Quick Start (3 Steps)

### Step 1: Import Collection

1. Open **Postman**
2. Click **Import** button (top left)
3. Drag and drop `E-Modal_API_Complete.postman_collection.json`
4. Click **Import**

### Step 2: Import Environment

1. Click **Import** button again
2. Drag and drop `E-Modal_API_Complete.postman_environment.json`
3. Click **Import**

### Step 3: Activate Environment

1. Click the **Environment dropdown** (top right corner)
2. Select **"E-Modal API - Complete Environment"**
3. ✅ **Done! All credentials are pre-configured**

---

## 📋 What's Included

### ✅ Pre-Configured Credentials (No Manual Entry Needed!)

| Variable | Value | Purpose |
|----------|-------|---------|
| `base_url` | `http://37.60.243.201:5000` | API server URL |
| `admin_key` | `6G8NlWa8W38MYTis` | Admin authentication |
| `user_token` | `TWDy1cZoqK9h` | User authentication |
| `user_id` | `1` | User ID (Juan Fernandez) |
| `emodal_username` | `jfernandez` | E-Modal login |
| `emodal_password` | `taffie` | E-Modal password |
| `emodal_captcha_key` | `7bf85bb6f37c9799543a2a463aab2b4f` | 2captcha API key |
| `query_id` | `q_1_1759809697` | Example query ID |
| `container_number` | `MSCU5165756` | Example container |

**✨ All values are already filled in - just import and use!**

---

## 📚 API Endpoints Organized by Category

### 1️⃣ **System** (2 endpoints)
- ✅ Health Check
- ✅ Root

### 2️⃣ **Admin - User Management** (5 endpoints)
- 📋 List All Users
- 👤 Get User by ID
- ➕ Create User
- 🔧 Update User Credentials
- ❌ Delete User

### 3️⃣ **Queries** (5 endpoints)
- 🚀 Trigger Query (E-Modal)
- 📋 List Queries
- 🔍 Get Query Details
- 📦 Download Query (ZIP)
- ❌ Delete Query

### 4️⃣ **Files - Master** (4 endpoints)
- 📄 Get Latest Containers
- 📅 Get Latest Appointments
- 🔄 Update Containers (Fetch from E-Modal)
- 🔄 Update Appointments (Fetch from E-Modal)

### 5️⃣ **Files - Query Specific** (5 endpoints)
- 📄 Get Query All Containers
- 🎯 Get Query Filtered Containers
- 📅 Get Query All Appointments
- 📝 Get Response File
- 📸 Get Screenshot File

### 6️⃣ **Files - Container Specific** (3 endpoints)
- 📸 Get Container Screenshots (ZIP)
- 📝 Get Container Responses (ZIP)
- 🗓️ Get Upcoming Appointments (N Days)

### 7️⃣ **Files - Filtered Containers** (2 endpoints)
- 📊 Get All Filtered Containers (Merged)
- 🎯 Get Latest Filtered Containers

### 8️⃣ **Schedule Management** (4 endpoints)
- 🔍 Get Schedule
- 🔧 Update Schedule
- ⏸️ Pause Schedule
- ▶️ Resume Schedule

**Total: 30 endpoints ready to test!**

---

## 🎯 Common Testing Scenarios

### Scenario 1: Run Your First Query

1. **Trigger Query**
   - Select: `Queries → Trigger Query (E-Modal)`
   - Click **Send**
   - Note the `query_id` from response

2. **Check Status**
   - Select: `Queries → List Queries`
   - Click **Send**
   - Find your query and check its status

3. **Get Results**
   - Update `query_id` variable (or use from response)
   - Select: `Files - Query Specific → Get Query Filtered Containers`
   - Click **Send**
   - Excel file will be downloaded

### Scenario 2: Get Containers with Upcoming Appointments

1. Select: `Files - Container Specific → Get Upcoming Appointments (N Days)`
2. Click **Send**
3. Response will show containers with appointments in next 3 days
4. Screenshot URLs are public (no authentication needed)

### Scenario 3: Download Container History

1. Update `container_number` variable with your container
2. Select: `Files - Container Specific → Get Container Screenshots (ZIP)`
3. Click **Send**
4. ZIP file with all screenshots will be downloaded

### Scenario 4: Get Merged Filtered Containers

1. Select: `Files - Filtered Containers → Get All Filtered Containers (Merged)`
2. Click **Send**
3. Excel file with all unique containers (latest version of each) will be downloaded

---

## 🔧 Customizing Variables

### To Update Query ID After Running a Query:

**Option 1: Manually**
1. Click **Environment quick look** (eye icon, top right)
2. Click **Edit** next to "E-Modal API - Complete Environment"
3. Update `query_id` value
4. Click **Save**

**Option 2: From Response**
1. After triggering a query, note the `query_id` in response
2. Update the variable as shown above

### To Test with Different Container:

1. Update `container_number` variable
2. Update `response_filename` and `screenshot_filename` if testing file endpoints

---

## 💡 Tips & Tricks

### ✅ Authentication is Automatic
All requests use the pre-configured tokens from environment variables:
- Admin endpoints: `{{admin_key}}`
- User endpoints: `{{user_token}}`

### ✅ Platform Support
Query trigger endpoint supports `platform` parameter:
```json
{
  "platform": "emodal"
}
```

### ✅ Query Parameters
Some endpoints have optional query parameters:
- **List Queries**: `?status=completed&limit=50&offset=0`
- **Upcoming Appointments**: `?days=3`
- **Response File**: `?download=true`

### ✅ View Response JSON in Browser
Set `download=false` (or omit) in "Get Response File" to view JSON in browser instead of downloading.

---

## 📊 Testing Workflow

### Complete Testing Flow:

```
1. Health Check → Verify system is running
2. List Users → Confirm user exists
3. Get User → Check user details
4. Trigger Query → Start a new query
5. List Queries → Monitor progress
6. Get Query Details → Check completion
7. Get Query Filtered Containers → Download results
8. Get Upcoming Appointments → Check upcoming slots
9. Get Container Screenshots → Download screenshots
10. Get All Filtered Containers → Export all data
```

---

## 🚨 Troubleshooting

### Problem: "Unauthorized" Error
**Solution:** 
1. Check environment is selected (top right)
2. Verify `user_token` or `admin_key` in environment
3. Ensure token hasn't been regenerated on server

### Problem: "Query not found"
**Solution:**
1. Update `query_id` variable with valid query ID
2. Run "List Queries" to get available query IDs

### Problem: "Container not found"
**Solution:**
1. Run a query first to generate container data
2. Update `container_number` with an existing container

### Problem: Request hangs for long time
**Solution:**
- Normal for:
  - **Trigger Query**: Can take 10-40 minutes
  - **Update Containers/Appointments**: Can take 5-10 minutes
- Postman default timeout: 30 minutes
- Check query status using "List Queries"

---

## 📝 Environment Variables Reference

### Server Configuration
```javascript
base_url = "http://37.60.243.201:5000"  // Main API server
```

### Authentication
```javascript
admin_key = "6G8NlWa8W38MYTis"  // For admin endpoints
user_token = "TWDy1cZoqK9h"      // For user endpoints
```

### User Information
```javascript
user_id = "1"
user_name = "Juan Fernandez"
user_username = "jfernandez"
```

### E-Modal Credentials
```javascript
emodal_username = "jfernandez"
emodal_password = "taffie"
emodal_captcha_key = "7bf85bb6f37c9799543a2a463aab2b4f"
```

### Query/Container Placeholders
```javascript
query_id = "q_1_1759809697"               // Update after running query
container_number = "MSCU5165756"          // Example container
response_filename = "MSCU5165756_*.json"  // Example response file
screenshot_filename = "MSCU5165756_*.png" // Example screenshot
```

---

## 🎓 Advanced Features

### Bulk Testing
Use Postman **Collection Runner**:
1. Right-click collection
2. Click **Run collection**
3. Select requests to run
4. Click **Run E-Modal API...**

### Automated Tests
Add tests to requests (Tests tab):
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has success", function () {
    pm.expect(pm.response.json().success).to.be.true;
});
```

### Export Results
After running requests:
1. Click **Runner** results
2. Click **Export Results**
3. Save as JSON

---

## 🔄 Keeping Environment Updated

### After Running a Query:
1. Copy `query_id` from response
2. Update in environment
3. Now you can test query-specific endpoints

### After Getting Query List:
1. Pick any `query_id` from the list
2. Update environment variable
3. Test with that specific query

### For Container Testing:
1. Download filtered containers
2. Pick any container number
3. Update `container_number` variable
4. Test container-specific endpoints

---

## 📞 Support

- **Documentation**: See `README.md` for API details
- **Testing**: See `TESTING_GUIDE.md` for test scripts
- **Interactive Tests**: Run `python test_interactive.py`

---

## ✨ Summary

### What You Get:
- ✅ **30 pre-configured endpoints** ready to test
- ✅ **All credentials pre-filled** - no manual entry needed
- ✅ **Organized by category** for easy navigation
- ✅ **Platform support** for future expansion
- ✅ **Query parameters** pre-configured with sensible defaults
- ✅ **Examples** for common testing scenarios

### Just 3 Steps:
1. Import collection
2. Import environment
3. Select environment → **Start testing!**

**No configuration needed - everything is ready to use! 🚀**


