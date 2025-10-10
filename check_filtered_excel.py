import pandas as pd
import os
import sys

# Find the most recent query folder
base_path = r"storage\users\1\emodal\queries"

if not os.path.exists(base_path):
    print(f"[ERROR] Path not found: {base_path}")
    sys.exit(1)

# Get all query folders
query_folders = [f for f in os.listdir(base_path) if f.startswith('q_')]
if not query_folders:
    print("[ERROR] No query folders found")
    sys.exit(1)

# Sort by modification time
query_folders.sort(key=lambda x: os.path.getmtime(os.path.join(base_path, x)), reverse=True)
latest_query = query_folders[0]

print(f"{'='*80}")
print(f"  CHECKING LATEST QUERY: {latest_query}")
print(f"{'='*80}\n")

filtered_file = os.path.join(base_path, latest_query, 'filtered_containers.xlsx')

if not os.path.exists(filtered_file):
    print(f"[ERROR] Filtered file not found: {filtered_file}")
    sys.exit(1)

print(f"Reading: {filtered_file}\n")

# Read the Excel file
df = pd.read_excel(filtered_file)

print(f"Total Rows: {len(df)}")
print(f"Total Columns: {len(df.columns)}\n")

print(f"All Column Names:")
print(f"{'-'*80}")
for i, col in enumerate(df.columns, 1):
    print(f"{i:3d}. {col}")

print(f"\n{'='*80}")
print(f"  CHECKING FOR NEW FIELDS")
print(f"{'='*80}\n")

new_fields = [
    'Manifested',
    'First Appointment Available (Before)',
    'Departed Terminal',
    'First Appointment Available (After)',
    'Empty Received'
]

for field in new_fields:
    if field in df.columns:
        print(f"[OK] Found: {field}")
        # Show first 3 values
        values = df[field].head(3).tolist()
        print(f"  First 3 values: {values}")
    else:
        print(f"[MISSING] {field}")

print(f"\n{'='*80}")
print(f"  LAST 5 COLUMNS")
print(f"{'='*80}\n")

last_5 = list(df.columns[-5:])
for i, col in enumerate(last_5, len(df.columns) - 4):
    print(f"{i:3d}. {col}")

print(f"\n{'='*80}")

