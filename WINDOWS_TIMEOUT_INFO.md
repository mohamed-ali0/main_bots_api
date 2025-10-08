# Windows Timeout Behavior - Important Info

## ❌ Common Misconception:
**Windows does NOT have a 5-minute max timeout for HTTP requests.**

However, there ARE some Windows networking limits that could affect long requests:

---

## 🔍 Actual Windows Network Limits:

### 1. **TCP Keep-Alive (Default: 2 hours)**
- Windows TCP keep-alive for idle connections: ~7200 seconds
- This is for IDLE connections, not active requests
- **Not your issue**

### 2. **Connection Pool Keep-Alive**
- Python `requests` library connection pool timeout
- Default: No hard limit
- **Might need configuration**

### 3. **Socket Timeout (Default: None)**
- Python socket timeout: Can be set per request
- We're setting it to 2400 seconds (40 minutes)
- **Should be fine**

### 4. **Router/Firewall Timeouts (Variable)**
- Some routers drop "idle" connections after 5-10 minutes
- But this is for idle connections, not active data transfer
- **Could be an issue if E-Modal API is slow to respond**

### 5. **IIS/Web Server Timeouts (If applicable)**
- IIS default execution timeout: 90-300 seconds
- Only applies if Flask is behind IIS
- **Not applicable for `python app.py`**

---

## 🎯 Your Actual Issue:

Based on your symptoms (system stuck after sending bulk request), the issue is likely:

### **Most Likely: E-Modal API is genuinely slow**
- Processing 13 containers (10 IMPORT + 3 EXPORT) might take 5-10 minutes
- The API might be running Selenium, solving captchas, etc.
- **This is NORMAL** - just takes time

### **Possible: Connection appears idle to network equipment**
- If E-Modal API doesn't send any data for 5+ minutes
- Some routers/firewalls might drop the connection
- **Fix: Add TCP Keep-Alive to requests**

### **Unlikely: Windows timeout**
- Windows itself doesn't limit this
- **Not the issue**

---

## ✅ How to Fix:

### 1. **Add TCP Keep-Alive to Requests Session**
This tells Windows/routers to keep the connection alive even during long processing:

```python
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.connection import create_connection

# Configure keep-alive
class TCPKeepAliveAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['socket_options'] = [
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60),
            (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10),
            (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
        ]
        super().init_poolmanager(*args, **kwargs)
```

### 2. **Test E-Modal API Directly**
Check if the E-Modal API is actually responding:

```python
import requests
import time

start = time.time()
response = requests.post(
    'http://37.60.243.201:5010/get_info_bulk',
    json={
        'session_id': 'session_1759863751_-7951041044287417896',
        'import_containers': ['CAIU7181746'],
        'export_containers': [],
        'debug': False
    },
    timeout=2400
)
elapsed = time.time() - start
print(f"Response in {elapsed:.1f} seconds: {response.status_code}")
```

### 3. **Check E-Modal API Server Logs**
The E-Modal API server might be logging what it's doing.
Check if it's processing the request or if it's stuck.

---

## 🔧 What I'll Do Now:

1. Add TCP keep-alive to the requests session
2. Add a progress indicator (print dots every 30 seconds during wait)
3. Test if the issue is the request library or the E-Modal API

Let me implement these fixes!

