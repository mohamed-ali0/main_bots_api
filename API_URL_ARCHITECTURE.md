# API URL Architecture - Updated Design

## Overview

This document explains the updated architecture for file access and URL management in the E-Modal Management System.

## Key Principle

**The internal E-Modal API (port 5010) is for server-to-server communication ONLY.**

- Users should NEVER directly access the E-Modal API (port 5010)
- All user requests must go through our main API (port 5000)
- All files are downloaded from E-Modal API and stored locally
- All files are served to users through our authenticated endpoints

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         END USER                                 │
│                  (Web App / Mobile App)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (Port 5000)
                              │ + Bearer Token Authentication
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN API (Flask)                              │
│                   http://localhost:5000                          │
│                                                                   │
│  Endpoints:                                                       │
│  - GET  /files/containers                                        │
│  - GET  /files/queries/{query_id}/screenshots/{filename}         │
│  - GET  /files/download/master/{type}                            │
│  - GET  /files/download/query/{query_id}/{type}                  │
│  - GET  /files/download/temp/{user_id}/{filename}                │
│  - GET  /files/containers/upcoming-appointments                  │
│  - etc.                                                           │
│                                                                   │
│  All responses return URLs pointing back to port 5000            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (Internal Network)
                              │ Server-to-Server Only
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTERNAL E-MODAL API (Selenium)                     │
│                  http://localhost:5010                           │
│                                                                   │
│  Used internally by Main API to:                                 │
│  - Fetch container data from E-Modal website                     │
│  - Get appointment information                                   │
│  - Download screenshots                                          │
│  - Retrieve booking numbers                                      │
│                                                                   │
│  NOT accessible to end users                                     │
└─────────────────────────────────────────────────────────────────┘
```

## File Flow

### 1. Container Query Process

```
1. User calls: POST /queries/trigger (Port 5000)
   ↓
2. Main API calls: POST /get_containers (Port 5010)
   ← E-Modal API returns Excel file URL
   ↓
3. Main API downloads Excel file and saves locally
   → storage/users/{user_id}/emodal/all_containers.xlsx
   ↓
4. Main API processes containers and calls: POST /check_appointments (Port 5010)
   ← E-Modal API returns screenshot URLs (pointing to port 5010)
   ↓
5. Main API downloads screenshots and saves locally
   → storage/users/{user_id}/queries/{query_id}/containers_checking_attempts/screenshots/
   ↓
6. Main API saves response JSON (with original URLs for reference)
   → storage/users/{user_id}/queries/{query_id}/containers_checking_attempts/responses/
```

### 2. User Retrieves Files

```
User calls: GET /files/containers (Port 5000)
   ↓
Main API responds with JSON:
{
  "success": true,
  "filename": "all_containers.xlsx",
  "download_url": "http://localhost:5000/files/download/master/containers",
  "note": "Use Authorization header to download: Bearer {user_token}"
}
   ↓
User calls: GET /files/download/master/containers (Port 5000)
   + Authorization: Bearer {user_token}
   ↓
Main API serves local file:
   storage/users/{user_id}/emodal/all_containers.xlsx
```

### 3. User Views Upcoming Appointments

```
User calls: GET /files/containers/upcoming-appointments?days=3 (Port 5000)
   ↓
Main API:
   1. Scans local response JSON files
   2. Finds locally saved screenshot files
   3. Constructs URLs pointing to port 5000
   ↓
Main API responds:
{
  "containers": [
    {
      "container_number": "MSCU5165756",
      "screenshot_url": "http://localhost:5000/files/queries/q_1_123/screenshots/MSCU5165756_ss.png",
      "screenshot_filename": "MSCU5165756_ss.png"
    }
  ]
}
   ↓
User calls: GET /files/queries/q_1_123/screenshots/MSCU5165756_ss.png (Port 5000)
   + Authorization: Bearer {user_token}
   ↓
Main API serves local file:
   storage/users/{user_id}/queries/q_1_123/containers_checking_attempts/screenshots/MSCU5165756_ss.png
```

## API Responses - URL Format

### ✅ CORRECT: All URLs point to Main API (Port 5000)

```json
{
  "success": true,
  "download_url": "http://localhost:5000/files/download/master/containers",
  "screenshot_url": "http://localhost:5000/files/queries/q_1_123/screenshots/container.png"
}
```

### ❌ INCORRECT: URLs pointing to E-Modal API (Port 5010)

```json
{
  "success": true,
  "download_url": "http://localhost:5010/files/container.xlsx",  // WRONG!
  "screenshot_url": "http://37.60.243.201:5010/files/screenshot.png"  // WRONG!
}
```

## File Serving Endpoints

All file-serving endpoints on Main API (Port 5000) require authentication:

### 1. Master Files
- **GET** `/files/download/master/containers`
- **GET** `/files/download/master/appointments`

### 2. Query-Specific Files
- **GET** `/files/download/query/{query_id}/all-containers`
- **GET** `/files/download/query/{query_id}/filtered-containers`
- **GET** `/files/download/query/{query_id}/all-appointments`

### 3. Screenshots and Responses
- **GET** `/files/queries/{query_id}/screenshots/{filename}`
- **GET** `/files/queries/{query_id}/responses/{filename}`

### 4. Temporary Files (Zips, Merged Files)
- **GET** `/files/download/temp/{user_id}/{filename}`

## Security

### Authentication Required
- All Main API endpoints (Port 5000) require Bearer token authentication
- Users can only access their own files (enforced by user_id checks)

### Internal E-Modal API (Port 5010)
- Should be bound to `localhost` only (not exposed externally)
- Only accessible by Main API server
- No direct user access

## Benefits of This Architecture

1. **Security**: Single point of authentication and access control
2. **Consistency**: All user-facing URLs use the same base URL and port
3. **Flexibility**: Can change internal E-Modal API location without affecting users
4. **Audit Trail**: All file access logged through Main API
5. **File Persistence**: Files remain available even if E-Modal API restarts
6. **Rate Limiting**: Can implement rate limiting at Main API level
7. **Caching**: Can cache frequently accessed files
8. **Multi-tenancy**: Easy to scale with multiple E-Modal API instances

## Implementation Details

### Config Changes
- Removed `PUBLIC_EMODAL_API_URL` from config.py
- `EMODAL_API_URL` is for internal use only
- Added comments clarifying the separation

### Route Changes (routes/files.py)
- All file endpoints return JSON with `download_url` pointing to port 5000
- Separate download endpoints actually serve the files
- `get_containers_with_upcoming_appointments` constructs URLs from local files

### Test Script Changes (test_interactive.py)
- Updated to show download URLs and offer to download
- Screenshot download now requires authentication
- Updated messages to reflect authenticated access

## Migration Notes

If you have existing response JSON files with old URLs:
- They are kept for reference only
- The system now constructs new URLs from local file paths
- No need to update existing JSON files

## Future Enhancements

1. **CDN Integration**: Could add CDN for file serving while maintaining authentication
2. **File Cleanup**: Implement automated cleanup of old temp files
3. **Compression**: Compress files before serving to reduce bandwidth
4. **Streaming**: Implement chunked file serving for large files
5. **Webhooks**: Notify users when files are ready instead of polling

---

**Last Updated**: 2025-10-11
**Version**: 2.0


