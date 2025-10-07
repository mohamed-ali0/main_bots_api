# Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.9+ installed
- ✅ PostgreSQL installed and running
- ✅ Internal E-Modal API running on port 5010

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Edit the DATABASE_URL in your `.env` file (already created):

```env
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/emodal_db
```

Then create the database:

```bash
# Windows PowerShell
createdb emodal_db

# Or with psql
psql -U postgres -c "CREATE DATABASE emodal_db;"
```

### 3. Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. Update Configuration

Edit the `.env` file and update these values:

```env
SECRET_KEY=your-random-secret-key-here
ADMIN_SECRET_KEY=your-admin-key-here
EMODAL_API_URL=http://localhost:5010
```

### 5. Start the Server

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### 6. Test the System

Open a new terminal and run:

```bash
python test_system.py
```

## First User Creation

### Using cURL (Windows PowerShell):

```powershell
$headers = @{
    'X-Admin-Key' = 'your-admin-key-here'
    'Content-Type' = 'application/json'
}

$body = @{
    name = "John Doe"
    username = "jdoe"
    password = "secure_password"
    emodal_username = "jfernandez"
    emodal_password = "taffie"
    emodal_captcha_key = "7bf85bb6f37c9799543a2a463aab2b4f"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/admin/users" -Method Post -Headers $headers -Body $body
```

### Using Python:

```python
import requests

response = requests.post(
    'http://localhost:5000/admin/users',
    headers={'X-Admin-Key': 'your-admin-key-here'},
    json={
        'name': 'John Doe',
        'username': 'jdoe',
        'password': 'secure_password',
        'emodal_username': 'jfernandez',
        'emodal_password': 'taffie',
        'emodal_captcha_key': '7bf85bb6f37c9799543a2a463aab2b4f'
    }
)

data = response.json()
print(f"Token: {data['user']['token']}")
```

**Save the token** - you'll need it for API requests!

## Trigger Your First Query

```python
import requests

token = "YOUR_USER_TOKEN"

response = requests.post(
    'http://localhost:5000/queries/trigger',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.json())
```

## Check Query Status

```python
import requests

token = "YOUR_USER_TOKEN"

response = requests.get(
    'http://localhost:5000/queries',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.json())
```

## Common Issues

### Issue: "Connection refused" or "Cannot connect to server"

**Solution**: Make sure the Flask app is running:
```bash
python app.py
```

### Issue: "Database connection failed"

**Solution**: 
1. Check PostgreSQL is running
2. Verify DATABASE_URL in `.env` is correct
3. Ensure database exists: `createdb emodal_db`

### Issue: "Internal E-Modal API not responding"

**Solution**: Ensure your E-Modal API is running on the configured port (default: 5010)

### Issue: "Migration failed"

**Solution**: 
```bash
# Remove existing migrations
rm -rf migrations

# Reinitialize
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Next Steps

1. **Configure Scheduling**: Update schedule frequency for users
   ```python
   requests.put(
       'http://localhost:5000/schedule',
       headers={'Authorization': f'Bearer {token}'},
       json={'enabled': True, 'frequency': 60}  # 60 minutes
   )
   ```

2. **Download Results**: Get containers and appointments files
   ```python
   response = requests.get(
       'http://localhost:5000/files/containers',
       headers={'Authorization': f'Bearer {token}'}
   )
   with open('containers.xlsx', 'wb') as f:
       f.write(response.content)
   ```

3. **Monitor Logs**: Check `logs/app.log` for system activity

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use a production WSGI server (gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
   ```
3. Set up reverse proxy (nginx)
4. Enable HTTPS
5. Use strong SECRET_KEY and ADMIN_SECRET_KEY
6. Configure database backups
7. Set up monitoring and alerting

## Support

For detailed API documentation, see `README.md`

For issues:
1. Check logs in `logs/app.log`
2. Verify configuration in `.env`
3. Test with `test_system.py`

