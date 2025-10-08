#!/usr/bin/env python3
"""
Trigger First Real Query

This will start the complete query process:
1. Get all containers from E-Modal
2. Filter containers (Holds=NO, Pregate=N/A)
3. Skip EXPORT containers
4. Check each IMPORT container (get timeline, determine move type, check appointments)
5. Get all appointments
"""

import requests
import json
import os
import time

# Configuration
BASE_URL = "http://localhost:5000"
TOKEN = "TWDy1cZoqK9h"  # User token from database

token = TOKEN

print("=" * 80)
print("  TRIGGER FIRST REAL QUERY")
print("=" * 80)

print(f"\n[INFO] Using token: {token}")
print(f"[INFO] API URL: {BASE_URL}")

# Trigger query
print(f"\n[INFO] Triggering query...")
print(f"[INFO] This will:")
print(f"  1. Get all containers from E-Modal")
print(f"  2. Filter: Holds=NO, Pregate=N/A")
print(f"  3. Skip EXPORT containers")
print(f"  4. Check IMPORT containers (timeline -> move type -> appointments)")
print(f"  5. Get all appointments")
print(f"\n[WARNING] This may take 10-30 minutes depending on container count!")
print(f"\n[INFO] Starting query...")

try:
    response = requests.post(
        f"{BASE_URL}/queries/trigger",
        headers={"Authorization": f"Bearer {token}"},
        timeout=2400  # 40 minutes (gives buffer for 30min internal timeout)
    )
    
    print(f"\n[INFO] Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[SUCCESS] Query triggered!")
        print(json.dumps(data, indent=2))
        
        query_id = data.get('query_id')
        if query_id:
            print(f"\n[INFO] Query ID: {query_id}")
            print(f"\n[INFO] You can check status with:")
            print(f"  python check_query_status.py")
            print(f"\n[INFO] Or check the query folder:")
            print(f"  storage/users/1/emodal/queries/{query_id}/")
    else:
        print(f"\n[ERROR] HTTP {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print(f"\n[INFO] Request timed out after 30 minutes")
    print(f"[INFO] Query may still be running - check logs or query status")
except Exception as e:
    print(f"\n[ERROR] Failed to trigger query: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
