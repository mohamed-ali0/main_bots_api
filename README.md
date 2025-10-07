# E-Modal Management System

A Flask-based REST API system that manages multiple users with automated scheduling to collect container and appointment data from E-Modal platform.

## 🚀 Features

- **Multi-user Management**: Create and manage multiple users with individual E-Modal sessions
- **Automated Scheduling**: Hourly queries that automatically collect and archive data
- **Complete API**: RESTful endpoints for user management, query execution, and file access
- **Token-based Authentication**: Secure API access with generated tokens
- **File Storage**: Organized storage structure for containers, appointments, and checking attempts
- **Query History**: Full traceability of all queries with detailed statistics

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL database
- Internal E-Modal API running (default: http://localhost:5010)

## 🔧 Installation

### 1. Clone/Create the project

The project structure is already created with all necessary files.

### 2. Create a virtual environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL Database

```bash
# Create database
createdb emodal_db

# Or with specific user
createdb -U postgres emodal_db
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory (or use the existing one):

```env
# Flask
SECRET_KEY=your-super-secret-key-here
DEBUG=False

# Database
DATABASE_URL=postgresql://emodal_user:emodal_pass@localhost:5432/emodal_db

# Internal E-Modal API
EMODAL_API_URL=http://localhost:5010

# Admin
ADMIN_SECRET_KEY=your-admin-secret-key-here

# Storage
STORAGE_PATH=storage

# Logging
LOG_LEVEL=INFO
```

### 6. Initialize Database

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

## 🏃 Running the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

## 📚 API Documentation

### Authentication

- **Admin Endpoints**: Use `X-Admin-Key` header
- **User Endpoints**: Use `Authorization: Bearer {token}` header

### Endpoints

#### Health Check
```
GET /health
```

#### Admin Endpoints

**Create User**
```
POST /admin/users
Headers: X-Admin-Key: {admin_key}
Body: {
  "name": "John Doe",
  "username": "jdoe",
  "password": "secure_password",
  "emodal_username": "jfernandez",
  "emodal_password": "taffie",
  "emodal_captcha_key": "7bf85bb6f37c9799543a2a463aab2b4f"
}
```

**List Users**
```
GET /admin/users
Headers: X-Admin-Key: {admin_key}
```

**Get User Details**
```
GET /admin/users/{user_id}
Headers: X-Admin-Key: {admin_key}
```

**Update Credentials**
```
PUT /admin/users/{user_id}/credentials
Headers: X-Admin-Key: {admin_key}
Body: {
  "platform": "emodal",
  "credentials": {
    "username": "new_user",
    "password": "new_pass",
    "captcha_api_key": "new_key"
  }
}
```

**Delete User**
```
DELETE /admin/users/{user_id}/flush
Headers: X-Admin-Key: {admin_key}
```

#### Query Endpoints

**Trigger Query**
```
POST /queries/trigger
Headers: Authorization: Bearer {token}
```

**List Queries**
```
GET /queries?status=completed&limit=50&offset=0
Headers: Authorization: Bearer {token}
```

**Get Query Details**
```
GET /queries/{query_id}
Headers: Authorization: Bearer {token}
```

**Download Query**
```
GET /queries/{query_id}/download
Headers: Authorization: Bearer {token}
```

**Delete Query**
```
DELETE /queries/{query_id}
Headers: Authorization: Bearer {token}
```

#### File Endpoints

**Get Latest Containers**
```
GET /files/containers
Headers: Authorization: Bearer {token}
```

**Get Latest Appointments**
```
GET /files/appointments
Headers: Authorization: Bearer {token}
```

**Get Query Files**
```
GET /files/queries/{query_id}/all-containers
GET /files/queries/{query_id}/filtered-containers
GET /files/queries/{query_id}/all-appointments
GET /files/queries/{query_id}/responses/{filename}
GET /files/queries/{query_id}/screenshots/{filename}
Headers: Authorization: Bearer {token}
```

#### Schedule Endpoints

**Get Schedule**
```
GET /schedule
Headers: Authorization: Bearer {token}
```

**Update Schedule**
```
PUT /schedule
Headers: Authorization: Bearer {token}
Body: {
  "enabled": true,
  "frequency": 120
}
```

**Pause Schedule**
```
POST /schedule/pause
Headers: Authorization: Bearer {token}
```

**Resume Schedule**
```
POST /schedule/resume
Headers: Authorization: Bearer {token}
```

## 🧪 Testing

Run the test script to verify the system:

```bash
python test_system.py
```

This will:
1. Check server health
2. Create a test user
3. Trigger a query
4. List queries
5. Test schedule management

## 📁 File Storage Structure

```
storage/
└── users/
    └── {user_id}/
        ├── user_cre_env.json
        └── emodal/
            ├── all_containers.xlsx
            ├── all_appointments.xlsx
            └── queries/
                └── {query_id}/
                    ├── all_containers.xlsx
                    ├── filtered_containers.xlsx
                    ├── all_appointments.xlsx
                    └── containers_checking_attempts/
                        ├── screenshots/
                        │   └── {container}_{timestamp}.png
                        └── responses/
                            └── {container}_{timestamp}.json
```

## ⚠️ Important Notes

### TODO Items

The following functions need to be implemented based on the actual E-Modal API response structure:

1. **`determine_move_type_from_timeline()`** in `services/query_service.py`
   - Analyze timeline data to determine the correct move type
   - Possible values: DROP EMPTY, PICK UP EMPTY, DROP LOADED, PICK UP LOADED

2. **`extract_container_info_from_timeline()`** in `services/query_service.py`
   - Extract trucking_company, terminal, truck_plate, own_chassis from timeline
   - This information is needed for appointment checking

3. **Session Validation**
   - Add logic to verify E-Modal session is still valid before reusing

### Container Filtering Logic

The system filters containers based on:
- Column D (Hold) = "no"
- Column E (Pregate) in ["no", "NA", "****"]

Update the filtering logic in `QueryService._filter_containers()` if your Excel structure differs.

## 🔒 Security

- Change all default keys in production
- Use strong passwords for database
- Consider encrypting `user_cre_env.json` files
- Add rate limiting to prevent abuse
- Use HTTPS in production

## 📝 License

This project is proprietary software.

## 🤝 Support

For issues or questions, please contact the development team.

