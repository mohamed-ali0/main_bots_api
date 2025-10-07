"""
Test script for container filtering logic
Tests the filtering function that filters containers based on Hold and Pregate columns
"""

import pandas as pd
import os
import sys
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def filter_containers(containers_file, output_file=None):
    """
    Filter containers based on Holds and Pregate Ticket# columns
    
    Filtering logic:
    - Column 3 (Holds) = "NO"
    - Column 4 (Pregate Ticket#) is NaN OR contains asterisks
    
    Args:
        containers_file: Path to all_containers.xlsx
        output_file: Path to save filtered results (optional)
    
    Returns:
        tuple: (filtered_df, stats_dict)
    """
    print(f"[INFO] Reading containers from: {containers_file}")
    
    try:
        # Read Excel with keep_default_na=False to preserve "N/A" as strings instead of NaN
        df = pd.read_excel(containers_file, keep_default_na=False)
        total_count = len(df)
        
        print(f"[INFO] Total containers loaded: {total_count}")
        print(f"[INFO] Columns: {list(df.columns[:6])}")
        
        # Column 3: Holds
        # Column 4: Pregate Ticket#
        
        print(f"\n[DEBUG] Column 3 (Holds) analysis:")
        holds_vals = df.iloc[:, 3].astype(str).str.upper().str.strip().value_counts()
        print(holds_vals)
        
        print(f"\n[DEBUG] Column 4 (Pregate Ticket#) sample values:")
        print(df.iloc[:, 4].head(20))
        
        # Apply filtering
        print(f"\n[INFO] Applying filter...")
        
        # Holds = "NO"
        holds_condition = df.iloc[:, 3].astype(str).str.upper().str.strip() == "NO"
        print(f"  Holds='NO': {holds_condition.sum()} containers")
        
        # Pregate contains "N/A" (now properly read as string "N/A" instead of NaN)
        pregate_col = df.iloc[:, 4]
        pregate_condition = pregate_col.astype(str).str.upper().str.contains("N/A", regex=False, na=False)
        
        print(f"  Pregate contains 'N/A': {pregate_condition.sum()} containers")
        
        # Combine conditions
        filtered = df[holds_condition & pregate_condition]
        filtered_count = len(filtered)
        removed_count = total_count - filtered_count
        
        # Create statistics
        stats = {
            'total_containers': total_count,
            'filtered_containers': filtered_count,
            'removed_containers': removed_count,
            'holds_no_count': holds_condition.sum(),
            'pregate_nan_asterisk_count': pregate_condition.sum(),
            'filter_method': 'position',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n[SUCCESS] Filtering complete!")
        print(f"  Total containers:    {total_count}")
        print(f"  Filtered (pass):     {filtered_count}")
        print(f"  Removed (fail):      {removed_count}")
        print(f"  Filter rate:         {(filtered_count/total_count*100):.1f}%")
        
        # Show some examples of filtered containers
        if filtered_count > 0:
            print(f"\n[INFO] Sample of filtered containers (first 10):")
            print(filtered[['Container #', 'Holds', 'Pregate Ticket#']].head(10).to_string())
        else:
            print(f"\n[WARNING] No containers passed the filter!")
            print(f"\n[INFO] Containers with Holds='NO' but failed pregate check:")
            holds_no_df = df[holds_condition]
            if len(holds_no_df) > 0:
                print(holds_no_df[['Container #', 'Holds', 'Pregate Ticket#']].head(10).to_string())
        
        # Save to output file if specified
        if output_file:
            filtered.to_excel(output_file, index=False)
            print(f"\n[SUCCESS] Filtered containers saved to: {output_file}")
            print(f"[INFO] File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        
        return filtered, stats
        
    except Exception as e:
        print(f"[ERROR] Failed to process file: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def analyze_columns(containers_file):
    """
    Analyze the Excel file structure to understand columns
    """
    print_header("Column Analysis")
    
    try:
        df = pd.read_excel(containers_file)
        
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}\n")
        
        print("Column Details:")
        print("-" * 80)
        
        for i, col in enumerate(df.columns):
            print(f"\nColumn {i} (Excel: {chr(65+i) if i < 26 else '?'}): '{col}'")
            print(f"  Data type: {df[col].dtype}")
            print(f"  Non-null: {df[col].notna().sum()} / {len(df)}")
            
            # Show unique values if reasonable number
            unique_vals = df[col].unique()
            if len(unique_vals) <= 20:
                print(f"  Unique values ({len(unique_vals)}): {list(unique_vals)[:10]}")
            else:
                print(f"  Unique values: {len(unique_vals)} (too many to display)")
            
            # Show sample values
            sample = df[col].head(5).tolist()
            print(f"  Sample values: {sample}")
            
            if i >= 9:  # Show first 10 columns
                remaining = len(df.columns) - 10
                if remaining > 0:
                    print(f"\n... and {remaining} more columns")
                break
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze file: {e}")


def main():
    """Main function"""
    
    print_header("CONTAINER FILTERING TEST UTILITY")
    
    print("What would you like to do?")
    print("\n  1. Test filtering on containers file")
    print("  2. Analyze Excel file structure")
    print("  3. Quick test (auto-find and filter)")
    print("  0. Exit")
    
    choice = input("\nEnter choice (0-3): ").strip()
    
    if choice == '1':
        # Test filtering
        file_path = input("\nEnter path to all_containers.xlsx (or press Enter for storage\\users\\1\\emodal\\all_containers.xlsx): ").strip().strip('"').strip("'")
        if not file_path:
            file_path = r'storage\users\1\emodal\all_containers.xlsx'
        
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return
        
        output_file = input("Enter output filename [filtered_containers.xlsx]: ").strip() or "filtered_containers.xlsx"
        filter_containers(file_path, output_file)
    
    elif choice == '2':
        file_path = input("\nEnter path to all_containers.xlsx (or press Enter for storage\\users\\1\\emodal\\all_containers.xlsx): ").strip().strip('"').strip("'")
        if not file_path:
            file_path = r'storage\users\1\emodal\all_containers.xlsx'
        
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return
        
        analyze_columns(file_path)
    
    elif choice == '3':
        # Quick test - auto-find
        possible_paths = [
            r'storage\users\1\emodal\all_containers.xlsx',
            'storage/users/1/emodal/all_containers.xlsx',
            'all_containers.xlsx',
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                print(f"[INFO] Found: {path}")
                break
        
        if not file_path:
            print("[ERROR] No containers file found!")
            return
        
        output_file = f"filtered_containers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filter_containers(file_path, output_file)
    
    elif choice == '0':
        print("[INFO] Goodbye!")
    else:
        print("[ERROR] Invalid choice")


if __name__ == '__main__':
    # Check if file path provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "filtered_containers.xlsx"
        
        if os.path.exists(file_path):
            print_header("CONTAINER FILTERING - COMMAND LINE MODE")
            filter_containers(file_path, output_file)
        else:
            print(f"[ERROR] File not found: {file_path}")
            print("\nUsage:")
            print("  python test_filtering.py <input_file> [output_file]")
            print("\nExample:")
            print("  python test_filtering.py storage\\users\\1\\emodal\\all_containers.xlsx filtered.xlsx")
    else:
        # Interactive mode
        main()
