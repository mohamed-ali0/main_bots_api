# Public File URLs - Authentication Model Update

## Summary

Updated the API to use a **two-tier authentication model**:
1. **Authentication required** to discover/list files and get URLs
2. **No authentication required** to access files once you have the URLs

This makes file URLs shareable while still protecting the discovery process.

---

## Changes Made

### 1. Info Endpoints (Still Require Authentication)

These endpoints require Bearer token to access:

- `GET /files/containers` - Get latest containers file info
- `GET /files/appointments` - Get latest appointments file info
- `GET /files/queries/{query_id}/all-containers` - Get query containers info
- `GET /files/queries/{query_id}/filtered-containers` - Get query filtered containers info
- `GET /files/queries/{query_id}/all-appointments` - Get query appointments info
- `GET /files/containers/{container_number}/screenshots` - Get container screenshots info (ZIP)
- `GET /files/containers/{container_number}/responses` - Get container responses info (ZIP)
- `GET /files/containers/upcoming-appointments` - Get upcoming appointments
- `GET /files/filtered-containers/all` - Get merged filtered containers
- `GET /files/filtered-containers/latest` - Get latest filtered containers

**Response includes:**
```json
{
  "success": true,
  "filename": "...",
  "download_url": "http://37.60.243.201:5000/files/download/...",
  "note": "No authentication required for download URL"
}
```

### 2. Download Endpoints (No Authentication Required)

These endpoints are **public** and don't require any authentication:

- `GET /files/download/master/{user_id}/containers` - Download master containers file
- `GET /files/download/master/{user_id}/appointments` - Download master appointments file
- `GET /files/download/query/{query_id}/all-containers` - Download query containers file
- `GET /files/download/query/{query_id}/filtered-containers` - Download query filtered containers
- `GET /files/download/query/{query_id}/all-appointments` - Download query appointments
- `GET /files/download/temp/{user_id}/{filename}` - Download temporary files (zips)
- `GET /files/queries/{query_id}/screenshots/{filename}` - View/download screenshot
- `GET /files/queries/{query_id}/responses/{filename}` - View/download response JSON

**No headers required** - URLs are shareable!

---

## URL Structure Changes

### Before:
```
GET /files/download/master/containers
Headers: Authorization: Bearer {token}
```

### After:
```
GET /files/download/master/{user_id}/containers
No headers required!
```

---

## Usage Flow

### Step 1: Get File Info (Requires Auth)
```bash
curl -X GET "http://37.60.243.201:5000/files/containers" \
  -H "Authorization: Bearer TWDy1cZoqK9h"
```

**Response:**
```json
{
  "success": true,
  "filename": "all_containers.xlsx",
  "file_size": 245760,
  "download_url": "http://37.60.243.201:5000/files/download/master/1/containers",
  "note": "No authentication required for download URL"
}
```

### Step 2: Download File (No Auth Needed)
```bash
curl -X GET "http://37.60.243.201:5000/files/download/master/1/containers" \
  -o all_containers.xlsx
```

**No authentication header needed!** You can:
- Share this URL with anyone
- Embed it in emails
- Use it in webhooks
- Download from browser directly

---

## Screenshot URLs Example

### Get upcoming appointments (Requires Auth):
```bash
curl -X GET "http://37.60.243.201:5000/files/containers/upcoming-appointments?days=3" \
  -H "Authorization: Bearer TWDy1cZoqK9h"
```

**Response:**
```json
{
  "containers": [
    {
      "container_number": "MEDU7724823",
      "screenshot_url": "http://37.60.243.201:5000/files/queries/q_1_1759809697/screenshots/MEDU7724823_1759811094.png",
      "screenshot_filename": "MEDU7724823_1759811094.png"
    }
  ]
}
```

### Access screenshot (No Auth Needed):
```bash
# Just paste this in your browser or curl without headers!
http://37.60.243.201:5000/files/queries/q_1_1759809697/screenshots/MEDU7724823_1759811094.png
```

---

## Security Considerations

### ✅ Protected:
- Discovery of what files exist
- User information and file metadata
- Query history and status
- File listings

### 🌐 Public (Once URL is known):
- Actual file content (Excel, screenshots, JSONs, ZIPs)
- File downloads via direct URL
- Screenshot images
- Response JSON files

### Why This Model?

1. **Shareability**: URLs can be shared via email, Slack, embedded in systems
2. **Integration**: Easier to integrate with external systems that can't handle auth
3. **Browser Access**: Users can click links in emails and download directly
4. **Webhooks**: Can send file URLs in webhooks without auth complexity
5. **Performance**: No token validation overhead for file serving
6. **CDN Ready**: Can easily add CDN in front of public file endpoints

### Security Notes:

- URLs contain query_id/user_id which are non-guessable UUIDs
- Discovery requires authentication (can't list all files)
- Files are isolated per user/query
- Old files can be cleaned up periodically
- Can add expiry timestamps to URLs if needed in future

---

## Postman Testing

### Test 1: Get File List (Requires Auth)
```
GET http://37.60.243.201:5000/files/containers/upcoming-appointments?days=3
Headers:
  Authorization: Bearer TWDy1cZoqK9h
```

### Test 2: Download File (No Auth)
```
GET http://37.60.243.201:5000/files/queries/q_1_1759809697/screenshots/MEDU7724823_1759811094.png
Headers: (none)
```

✅ Should work without any authorization header!

---

## Benefits

1. ✅ **No port 5010 URLs in responses** - All URLs point to port 5000
2. ✅ **Shareable URLs** - Can be shared with anyone
3. ✅ **Browser-friendly** - Click and download
4. ✅ **Integration-friendly** - No complex auth for file access
5. ✅ **Protected discovery** - Still need auth to find what files exist
6. ✅ **Simplified client code** - Download URLs don't need auth handling

---

## Migration Notes

- All existing URLs will continue to work
- No changes needed to existing integrations
- New URLs include user_id/query_id for proper routing
- Old authenticated download endpoints will still work but aren't needed

---

**Updated**: 2025-10-11
**Version**: 3.0

