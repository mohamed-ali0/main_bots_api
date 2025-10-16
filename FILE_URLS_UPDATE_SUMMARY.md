# File URLs Update - Summary of Changes

## Problem

The system was returning URLs pointing to the internal E-Modal API (port 5010) in user-facing responses. This is incorrect because:
1. The internal E-Modal API (port 5010) should ONLY communicate with our main API (port 5000)
2. End users should NEVER directly access port 5010
3. All file access should go through our authenticated API endpoints (port 5000)

## Solution

Updated all file-returning endpoints to:
1. Return JSON responses with metadata instead of raw files
2. Provide download URLs pointing to OUR API (port 5000)
3. Require authentication for all file access
4. Serve files from local storage through authenticated endpoints

---

## Files Changed

### 1. `routes/files.py`

#### File Info Endpoints (Now Return JSON)
All these endpoints now return JSON with file info and download URL instead of raw files:

- **GET** `/files/containers`
- **GET** `/files/appointments`
- **GET** `/files/queries/{query_id}/all-containers`
- **GET** `/files/queries/{query_id}/filtered-containers`
- **GET** `/files/queries/{query_id}/all-appointments`
- **GET** `/files/containers/{container_number}/screenshots` (ZIP)
- **GET** `/files/containers/{container_number}/responses` (ZIP)
- **GET** `/files/filtered-containers/all` (Merged Excel)
- **GET** `/files/filtered-containers/latest`

**Response Format Example:**
```json
{
  "success": true,
  "file_type": "excel",
  "filename": "all_containers.xlsx",
  "file_size": 245760,
  "last_modified": "2025-10-11T10:30:00",
  "download_url": "http://localhost:5000/files/download/master/containers",
  "note": "Use Authorization header to download: Bearer {{user_token}}"
}
```

#### New Download Endpoints (Actually Serve Files)
Added three new authenticated download endpoints:

1. **GET** `/files/download/master/{file_type}`
   - For master files (containers, appointments)
   - Returns raw Excel file

2. **GET** `/files/download/query/{query_id}/{file_type}`
   - For query-specific files (all-containers, filtered-containers, all-appointments)
   - Returns raw Excel file

3. **GET** `/files/download/temp/{user_id}/{filename}`
   - For temporary files (zips, merged files)
   - Returns raw file (ZIP or Excel)

#### Updated Upcoming Appointments Endpoint
- **GET** `/files/containers/upcoming-appointments`
- Changed to construct screenshot URLs from LOCAL files
- URLs now point to `/files/queries/{query_id}/screenshots/{filename}` (port 5000)
- Previously was extracting URLs from E-Modal API responses (port 5010)

**Before:**
```json
{
  "screenshot_url": "http://37.60.243.201:5010/files/screenshot.png"  // WRONG!
}
```

**After:**
```json
{
  "screenshot_url": "http://localhost:5000/files/queries/q_1_123/screenshots/MSCU5165756_ss.png",
  "screenshot_filename": "MSCU5165756_ss.png"
}
```

### 2. `config.py`

**Removed:**
```python
PUBLIC_EMODAL_API_URL = os.getenv('PUBLIC_EMODAL_API_URL', 'http://37.60.243.201:5010')
```

**Updated:**
```python
# Internal E-Modal API (for server-to-server communication ONLY)
# This API should NOT be exposed to end users
# All client requests must go through our main API (port 5000)
EMODAL_API_URL = os.getenv('EMODAL_API_URL', 'http://localhost:5010')
```

### 3. `test_interactive.py`

Updated all test functions to handle the new JSON response format:

#### Modified Test Functions:
- `test_get_containers()` - Now shows file info and offers to download
- `test_get_appointments()` - Now shows file info and offers to download
- `test_get_query_files()` - Now shows file info and offers to download
- `test_get_container_screenshots()` - Now shows ZIP info and offers to download
- `test_get_container_responses()` - Now shows ZIP info and offers to download
- `test_get_all_filtered_containers()` - Now shows file info and offers to download
- `test_get_upcoming_appointments()` - Updated to use authenticated URLs

**Key Changes:**
1. Parse JSON response to get file metadata
2. Display file info (name, size, URL)
3. Prompt user if they want to download
4. If yes, make authenticated request to download_url
5. Screenshot downloads now require authentication

**Before:**
```python
# Screenshots were "public" URLs (port 5010)
ss_response = requests.get(ss_url, timeout=30)  # No auth
```

**After:**
```python
# Screenshots now require authentication (port 5000)
ss_response = requests.get(
    ss_url, 
    headers={'Authorization': f'Bearer {USER_TOKEN}'},
    timeout=30
)
```

### 4. `API_URL_ARCHITECTURE.md` (New File)

Comprehensive documentation explaining:
- Architecture diagram
- File flow for queries and retrieval
- Correct vs incorrect URL formats
- All file-serving endpoints
- Security model
- Benefits of the architecture
- Implementation details
- Future enhancements

---

## User Experience Changes

### Before
1. User calls `/files/containers`
2. Receives raw Excel file directly
3. No visibility into file metadata

### After
1. User calls `/files/containers`
2. Receives JSON with file info:
   ```json
   {
     "filename": "all_containers.xlsx",
     "file_size": 245760,
     "download_url": "http://localhost:5000/files/download/master/containers"
   }
   ```
3. User can decide whether to download
4. User calls the download_url to get the actual file
5. Same authentication token works for both requests

---

## Security Improvements

### 1. Single Authentication Point
- All file access goes through port 5000
- All requests require Bearer token authentication
- Consistent security model

### 2. Access Control
- Users can only access their own files
- Query ID validation ensures proper ownership
- User ID validation for temp files

### 3. Audit Trail
- All file access logged through Main API
- Can track who accessed what and when

### 4. Internal API Protection
- E-Modal API (port 5010) not exposed to users
- Can be bound to localhost only
- Server-to-server communication only

---

## Testing

### Test All Updated Endpoints
Run the interactive test script:
```bash
python test_interactive.py
```

Test these options:
- **17**: Get Latest Containers File (returns JSON, offers download)
- **18**: Get Latest Appointments File (returns JSON, offers download)
- **19**: Get Query-Specific Files (returns JSON, offers download)
- **24**: Get All Screenshots for Container (returns JSON, offers download)
- **25**: Get All Responses for Container (returns JSON, offers download)
- **26**: Get Containers with Upcoming Appointments (authenticated URLs)
- **27**: Get All Filtered Containers (returns JSON, offers download)
- **28**: Get Latest Filtered Containers (returns JSON, offers download)

### Verify URLs
Check that all URLs in responses:
- Point to port 5000 (not 5010)
- Use the correct format: `http://localhost:5000/files/download/...`
- Require authentication when accessed

---

## Migration Notes

### Existing Response JSON Files
- Old response JSONs may contain E-Modal API URLs (port 5010)
- These are kept for reference only
- System now constructs new URLs from local file paths
- No need to update existing JSON files

### No Breaking Changes for Existing Clients
The following endpoints still work the same way (serve raw files):
- `/files/queries/{query_id}/screenshots/{filename}`
- `/files/queries/{query_id}/responses/{filename}`

These are internal endpoints used by the system, not meant for direct user access.

---

## Future Considerations

1. **File Expiration**: Implement cleanup for old temp files in downloads folder
2. **Pagination**: For large file lists, add pagination to JSON responses
3. **Compression**: Compress files before serving to reduce bandwidth
4. **Caching**: Add caching headers to download responses
5. **Rate Limiting**: Implement rate limiting per user
6. **Webhooks**: Notify users when files are ready

---

## Summary

✅ All file URLs now point to our Main API (port 5000)
✅ All file access requires authentication
✅ Internal E-Modal API (port 5010) is isolated from users
✅ Consistent JSON response format with metadata
✅ Separate info and download endpoints for better control
✅ Updated test scripts to reflect new architecture
✅ Comprehensive documentation added

**Result**: Clean separation between internal E-Modal API and user-facing Main API, with proper authentication and access control.

---

**Date**: 2025-10-11
**Version**: 2.0


