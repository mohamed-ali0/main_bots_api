#!/usr/bin/env python3
"""
Simple query status checker - check specific query
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"
TOKEN = "TWDy1cZoqK9h"
QUERY_ID = "q_1_1759809010"

print("=" * 80)
print(f"  CHECKING QUERY: {QUERY_ID}")
print("=" * 80)

try:
    response = requests.get(
        f"{BASE_URL}/queries/{QUERY_ID}",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    
    print(f"\n[INFO] Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[RESULT]")
        print(json.dumps(data, indent=2))
    else:
        print(f"\n[ERROR] HTTP {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n[ERROR] Failed to check query: {e}")

print("\n" + "=" * 80)
