# Excel Sheet Column Structure

## Column Mapping (Letter -> Name -> Index)

| Letter | Column Name | Index | Description |
|--------|-------------|-------|-------------|
| A | Container # | 0 | Container number |
| B | Trade Type | 1 | IMPORT/EXPORT |
| C | Status | 2 | Container status (GATE OUT, GATE IN, IN YARD, ON VESSEL, etc.) |
| D | Holds | 3 | Hold status (NO/YES) |
| E | Pregate Ticket# | 4 | Pregate ticket number |
| F | Emodal Pregate Status | 5 | Pregate status in E-Modal |
| G | Gate Status | 6 | Gate status |
| H | Origin | 7 | Origin location |
| I | Destination | 8 | Destination location |
| J | Current Location | 9 | Current location/terminal |
| K | Line | 10 | Shipping line |
| L | Vessel Name | 11 | Vessel name |
| M | Vessel Code | 12 | Vessel code |
| N | Voyage | 13 | Voyage number |
| O | Size Type | 14 | Container size/type |
| P | Fees | 15 | Associated fees |
| Q | LFD/GTD | 16 | Last Free Day/Gate Turn Date |
| R | Tags | 17 | Additional tags |

## Pandas DataFrame Access

When reading Excel with pandas, you can access columns by:
- **Index**: `df.iloc[:, 0]` for Container #
- **Name**: `df['Container #']` if using column names
- **Row as dict**: `row_dict = row.to_dict()` then `row_dict['Container #']`

## Filtered Containers

The system filters containers where:
- **Column D (Holds)** = "NO"
- **Column E (Pregate Ticket#)** contains "N/A"

## Next: Logic Needed

Now that we have the column structure, please provide logic for:

1. **Terminal Code**: Which column contains the terminal code? (Likely Column J: Current Location?)
   - Is it in format like "TTI", "ITS", "PCT"?
   
2. **Move Type Logic**: Based on Trade Type (B) and Status (C), how to determine:
   - PICK FULL
   - DROP FULL
   - PICK EMPTY
   - DROP EMPTY
   
3. **Trucking Company**: How to choose between:
   - K & R TRANSPORTATION LLC
   - California Cartage Express

4. **Timeline Extraction**: What information to extract from timeline response?

