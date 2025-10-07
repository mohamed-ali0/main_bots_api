#!/usr/bin/env python3
"""
Test Script for Container Logic with Filtered Sheet

This script:
1. Reads the filtered containers from Excel
2. Tests the logic for each container (terminal, move type, trucking company)
3. Generates mock requests to verify the logic is implemented correctly
4. Does NOT actually call the API - just validates the logic
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Import the logic functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.query_service import (
    determine_terminal,
    determine_move_type,
    determine_trucking_company,
    QueryService
)

def test_container_logic(containers_file):
    """
    Test the container logic with filtered containers
    
    Args:
        containers_file: Path to filtered containers Excel file
    """
    print("=" * 80)
    print("  CONTAINER LOGIC TEST")
    print("=" * 80)
    
    try:
        # Read filtered containers
        print(f"\n[INFO] Reading filtered containers from: {containers_file}")
        df = pd.read_excel(containers_file, keep_default_na=False)
        
        print(f"[INFO] Total containers loaded: {len(df)}")
        print(f"[INFO] Columns: {list(df.columns)}")
        
        # Get terminal mapping and trucking companies from QueryService
        terminal_mapping = QueryService.TERMINAL_MAPPING
        trucking_companies = QueryService.TRUCKING_COMPANIES
        
        # Test results
        test_results = []
        
        print(f"\n[INFO] Testing logic for each container...")
        print("=" * 80)
        
        for idx, row in df.iterrows():
            container_data = row.to_dict()
            container_number = str(container_data.get('Container #', '')).strip()
            trade_type = str(container_data.get('Trade Type', '')).strip().upper()
            status = str(container_data.get('Status', '')).strip()
            
            print(f"\n[{idx+1}/{len(df)}] Container: {container_number}")
            print(f"  Trade Type: {trade_type}")
            print(f"  Status: {status}")
            
            # Test terminal determination
            terminal = determine_terminal(container_data, terminal_mapping)
            print(f"  > Terminal: {terminal}")
            
            # Test trucking company
            trucking_company = determine_trucking_company(container_data, trucking_companies)
            print(f"  > Trucking Company: {trucking_company}")
            
            # Test move type (with mock timeline for IMPORT)
            mock_timeline = {
                'success': True,
                'passed_pregate': False  # Mock: can be True or False
            }
            move_type = determine_move_type(container_data, mock_timeline if trade_type == 'IMPORT' else None)
            print(f"  > Move Type: {move_type}")
            
            # Determine identifier
            if trade_type == 'IMPORT':
                identifier = container_number
                needs_timeline = True
                needs_booking = False
            else:
                identifier = f"BOOKING_{container_number}"  # Mock booking number
                needs_timeline = False
                needs_booking = True
            
            print(f"  > Identifier: {identifier}")
            print(f"  > Needs Timeline: {needs_timeline}")
            print(f"  > Needs Booking Number: {needs_booking}")
            
            # Store result
            test_results.append({
                'Container #': container_number,
                'Trade Type': trade_type,
                'Status': status,
                'Terminal': terminal,
                'Trucking Company': trucking_company,
                'Move Type': move_type,
                'Identifier': identifier,
                'Needs Timeline': needs_timeline,
                'Needs Booking': needs_booking,
                'Terminal Valid': terminal is not None
            })
        
        print("\n" + "=" * 80)
        print("  TEST SUMMARY")
        print("=" * 80)
        
        # Summary statistics
        total = len(test_results)
        import_count = sum(1 for r in test_results if r['Trade Type'] == 'IMPORT')
        export_count = sum(1 for r in test_results if r['Trade Type'] == 'EXPORT')
        valid_terminals = sum(1 for r in test_results if r['Terminal Valid'])
        
        print(f"\n[SUMMARY] Total Containers: {total}")
        print(f"[SUMMARY] IMPORT Containers: {import_count}")
        print(f"[SUMMARY] EXPORT Containers: {export_count}")
        print(f"[SUMMARY] Valid Terminals: {valid_terminals}/{total}")
        
        # Move type distribution
        move_types = {}
        for r in test_results:
            mt = r['Move Type']
            move_types[mt] = move_types.get(mt, 0) + 1
        
        print(f"\n[SUMMARY] Move Type Distribution:")
        for mt, count in move_types.items():
            print(f"  - {mt}: {count} containers")
        
        # Terminal distribution
        terminals = {}
        for r in test_results:
            term = r['Terminal'] or 'UNKNOWN'
            terminals[term] = terminals.get(term, 0) + 1
        
        print(f"\n[SUMMARY] Terminal Distribution:")
        for term, count in sorted(terminals.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {term}: {count} containers")
        
        # Export detailed results to CSV
        results_df = pd.DataFrame(test_results)
        output_file = 'logic_test_results.csv'
        results_df.to_csv(output_file, index=False)
        print(f"\n[SUCCESS] Detailed results saved to: {output_file}")
        
        # Check for issues
        issues = []
        for r in test_results:
            if not r['Terminal Valid']:
                issues.append(f"  - {r['Container #']}: No terminal found")
        
        if issues:
            print(f"\n[WARNING] Found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10
                print(issue)
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")
        else:
            print(f"\n[SUCCESS] All containers have valid logic!")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"[ERROR] Failed to test logic: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("  CONTAINER LOGIC TEST UTILITY")
    print("=" * 80)
    
    # Default file paths to try
    default_paths = [
        "final_correct_all.xlsx",
        "final_proper_na_corrected.xlsx",
        "storage/users/1/emodal/filtered_containers.xlsx",
        "test_filtered.xlsx"
    ]
    
    containers_file = None
    
    # Check if file provided as argument
    if len(sys.argv) > 1:
        containers_file = sys.argv[1]
        if not os.path.exists(containers_file):
            print(f"[ERROR] File not found: {containers_file}")
            containers_file = None
    
    # Try default paths if no valid file provided
    if not containers_file:
        print("\n[INFO] No file specified, trying default paths...")
        for path in default_paths:
            if os.path.exists(path):
                containers_file = path
                print(f"[INFO] Found file: {path}")
                break
    
    if not containers_file:
        print(f"\n[ERROR] No containers file found. Please provide a path:")
        print(f"Usage: python test_logic_with_filtered.py <path_to_filtered_containers.xlsx>")
        return
    
    # Run the test
    test_container_logic(containers_file)

if __name__ == "__main__":
    main()
