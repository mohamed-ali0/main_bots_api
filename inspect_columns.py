"""Quick script to inspect containers file columns"""
import pandas as pd

file_path = r'storage\users\1\emodal\all_containers.xlsx'

df = pd.read_excel(file_path)

print("Column Analysis:")
print("=" * 80)

# Check columns 3 and 4
print(f"\nColumn 3 (D): '{df.columns[3]}'")
print(f"Unique values:")
print(df.iloc[:, 3].value_counts())

print(f"\n" + "=" * 80)
print(f"\nColumn 4 (E): '{df.columns[4]}'")
print(f"Unique values:")
print(df.iloc[:, 4].value_counts())

print(f"\n" + "=" * 80)
print(f"\nSample rows:")
print(df[['Container #', df.columns[3], df.columns[4]]].head(10))


