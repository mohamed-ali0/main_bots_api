#!/usr/bin/env python3
"""
Test Real Implementation - Actual API Calls

This script tests the real implementation with actual API calls:
1. One IMPORT container (get timeline, determine move type, check appointments)
2. One EXPORT container (get booking number, check appointments)
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.emodal_client import EModalClient
from services.query_service import get_check, QueryService
from models import db, User
from flask import Flask

# Create Flask app for database context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///emodal.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def load_user_session():
    """Load user and session from database"""
    with app.app_context():
        user = User.query.first()
        if not user:
            print("[ERROR] No user found in database. Run add_user.py first.")
            return None, None
        
        print(f"[INFO] Loaded user: {user.name} (ID: {user.id})")
        
        # Load credentials from file
        cred_file = os.path.join(user.folder_path, 'user_cre_env.json')
        if not os.path.exists(cred_file):
            print(f"[ERROR] Credentials file not found: {cred_file}")
            return None, None
        
        with open(cred_file, 'r') as f:
            creds = json.load(f)
        
        emodal_creds = creds.get('emodal', {})
        if not all([emodal_creds.get('username'), emodal_creds.get('password'), emodal_creds.get('captcha_api_key')]):
            print("[ERROR] Missing E-Modal credentials in file")
            return None, None
        
        print(f"[INFO] Loaded credentials for: {emodal_creds['username']}")
        
        # Create new session if needed
        session_id = user.session_id
        if not session_id:
            print("[INFO] No session_id in database, will create new session")
        else:
            print(f"[INFO] Existing Session ID: {session_id[:30]}...")
        
        return user, session_id, emodal_creds

def test_real_implementation():
    """Test real implementation with API calls"""
    print("=" * 80)
    print("  REAL IMPLEMENTATION TEST - WITH ACTUAL API CALLS")
    print("=" * 80)
    
    # Load filtered containers
    containers_file = "final_proper_na_corrected.xlsx"
    if not os.path.exists(containers_file):
        print(f"[ERROR] Filtered containers file not found: {containers_file}")
        return
    
    print(f"\n[INFO] Reading filtered containers from: {containers_file}")
    df = pd.read_excel(containers_file, keep_default_na=False)
    print(f"[INFO] Total containers: {len(df)}")
    
    # Find one IMPORT and one EXPORT
    import_containers = df[df['Trade Type'].str.upper() == 'IMPORT']
    export_containers = df[df['Trade Type'].str.upper() == 'EXPORT']
    
    if len(import_containers) == 0:
        print("[ERROR] No IMPORT containers found")
        return
    
    if len(export_containers) == 0:
        print("[ERROR] No EXPORT containers found")
        return
    
    # Select test containers
    import_container = import_containers.iloc[0]
    export_container = export_containers.iloc[0]
    
    import_number = import_container['Container #']
    export_number = export_container['Container #']
    
    print(f"\n[INFO] Selected IMPORT container: {import_number}")
    print(f"[INFO] Selected EXPORT container: {export_number}")
    
    # Load user and session
    print(f"\n[INFO] Loading user and session...")
    result = load_user_session()
    if not result:
        return
    user, session_id, emodal_creds = result
    
    # Initialize E-Modal client
    emodal_api_url = os.getenv('EMODAL_API_URL', 'http://localhost:5010')
    print(f"\n[INFO] E-Modal API URL: {emodal_api_url}")
    emodal_client = EModalClient(emodal_api_url)
    
    # Use existing session
    if not session_id:
        print(f"[ERROR] No session_id found. Please set a valid session first.")
        return
    
    print(f"[INFO] Using existing session: {session_id[:40]}...")
    
    # Get mappings
    terminal_mapping = QueryService.TERMINAL_MAPPING
    trucking_companies = QueryService.TRUCKING_COMPANIES
    
    # Create test query folder
    query_folder = os.path.join('storage', 'users', str(user.id), 'emodal', 'queries', 'test_real_impl')
    os.makedirs(query_folder, exist_ok=True)
    
    print("\n" + "=" * 80)
    print("  TEST 1: IMPORT CONTAINER")
    print("=" * 80)
    
    print(f"\n[INFO] Testing IMPORT container: {import_number}")
    print(f"[INFO] This will:")
    print(f"  1. Call get_container_timeline() API")
    print(f"  2. Check passed_pregate from timeline")
    print(f"  3. Determine move type (DROP EMPTY or PICK FULL)")
    print(f"  4. Call check_appointments() API with container number")
    print(f"\n[INFO] Starting API calls...")
    
    import_data = import_container.to_dict()
    
    try:
        result_import = get_check(
            emodal_client=emodal_client,
            session_id=session_id,
            container_data=import_data,
            query_folder=query_folder,
            terminal_mapping=terminal_mapping,
            trucking_companies=trucking_companies
        )
        
        print(f"\n[RESULT] IMPORT Container: {import_number}")
        print(f"  Success: {result_import.get('success')}")
        print(f"  Trade Type: {result_import.get('trade_type')}")
        print(f"  Terminal: {result_import.get('terminal')}")
        print(f"  Move Type: {result_import.get('move_type')}")
        print(f"  Available Times: {len(result_import.get('available_times', []))} slots")
        
        if result_import.get('error'):
            print(f"  Error: {result_import.get('error')}")
        
        if result_import.get('response_path'):
            print(f"  Response saved: {result_import.get('response_path')}")
        
        if result_import.get('screenshot_path'):
            print(f"  Screenshot saved: {result_import.get('screenshot_path')}")
            
    except Exception as e:
        print(f"[ERROR] IMPORT test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("  TEST 2: EXPORT CONTAINER")
    print("=" * 80)
    
    print(f"\n[INFO] Testing EXPORT container: {export_number}")
    print(f"[INFO] This will:")
    print(f"  1. Call get_booking_number() API")
    print(f"  2. Get booking number from response")
    print(f"  3. Move type = DROP FULL (always for EXPORT)")
    print(f"  4. Call check_appointments() API with booking number")
    print(f"\n[INFO] Starting API calls...")
    
    export_data = export_container.to_dict()
    
    try:
        result_export = get_check(
            emodal_client=emodal_client,
            session_id=session_id,
            container_data=export_data,
            query_folder=query_folder,
            terminal_mapping=terminal_mapping,
            trucking_companies=trucking_companies
        )
        
        print(f"\n[RESULT] EXPORT Container: {export_number}")
        print(f"  Success: {result_export.get('success')}")
        print(f"  Trade Type: {result_export.get('trade_type')}")
        print(f"  Terminal: {result_export.get('terminal')}")
        print(f"  Booking Number: {result_export.get('booking_number')}")
        print(f"  Move Type: {result_export.get('move_type')}")
        print(f"  Available Times: {len(result_export.get('available_times', []))} slots")
        
        if result_export.get('error'):
            print(f"  Error: {result_export.get('error')}")
        
        if result_export.get('response_path'):
            print(f"  Response saved: {result_export.get('response_path')}")
        
        if result_export.get('screenshot_path'):
            print(f"  Screenshot saved: {result_export.get('screenshot_path')}")
            
    except Exception as e:
        print(f"[ERROR] EXPORT test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("  TEST COMPLETE")
    print("=" * 80)
    print(f"\n[INFO] Check the query folder for saved responses and screenshots:")
    print(f"  {query_folder}")
    print("\n")

def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("  REAL IMPLEMENTATION TEST UTILITY")
    print("=" * 80)
    print("\n[WARNING] This will make REAL API calls to E-Modal!")
    print("[WARNING] Make sure the E-Modal API server is running.")
    print("[WARNING] This may take several minutes.")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("[INFO] Test cancelled.")
        return
    
    test_real_implementation()

if __name__ == "__main__":
    main()
