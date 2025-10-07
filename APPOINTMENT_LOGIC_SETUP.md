# Appointment Check Logic Setup

## System Configuration Complete

I've added the following to the system:

### 1. Terminal Mappings
```python
TERMINAL_MAPPING = {
    'ETSLAX': 'Everport Terminal Services - Los Angeles',
    'ETSOAK': 'Everport Terminal Services - Oakland',
    'ETSTAC': 'Everport Terminal Services Inc. - Tacoma, WA',
    'FIT': 'Florida International Terminal (FIT)',
    'HUSKY': 'Husky Terminal and Stevedoring, Inc.',
    'ITS': 'ITS Long Beach',
    'OICT': 'OICT',
    'PCT': 'Pacific Container Terminal',
    'PACKR': 'Packer Avenue Marine Terminal',
    'PET': 'Port Everglades Terminal',
    'SSA': 'SSA Terminal - PierA / LB',
    'SSAT30': 'SSAT - Terminal 30',
    'SSAT5': 'SSAT - Terminal 5',
    'T18': 'Terminal 18',
    'TTI': 'Total Terminals Intl LLC',
    'TRPOAK': 'TraPac - Oakland',
    'TRP1': 'TraPac LLC - Los Angeles',
    'WUT': 'Washington United Terminals'
}
```

### 2. Trucking Companies
```python
TRUCKING_COMPANIES = [
    'K & R TRANSPORTATION LLC',
    'California Cartage Express'
]
```

### 3. Move Types
```python
MOVE_TYPES = [
    'PICK FULL',
    'DROP FULL',
    'PICK EMPTY',
    'DROP EMPTY'
]
```

## Functions Awaiting Your Logic

### Function 1: `determine_terminal(container_data, terminal_mapping)`
**Purpose:** Extract terminal code from Excel data and map it to full terminal name

**You need to tell me:**
- Which column in the Excel sheet contains the terminal code?
- How to extract it from the container_data?

**Example:**
```python
def determine_terminal(container_data, terminal_mapping):
    # YOUR LOGIC HERE:
    # terminal_code = container_data['column_name']  # Which column?
    # return terminal_mapping.get(terminal_code)
    pass
```

---

### Function 2: `determine_move_type(container_data, timeline_response)`
**Purpose:** Determine which move type to use based on container data and timeline

**You need to tell me:**
- What rules determine if it's PICK vs DROP?
- What rules determine if it's FULL vs EMPTY?
- What data from Excel should I check? (Trade Type? Status? Other columns?)
- What data from timeline should I check?

**Example:**
```python
def determine_move_type(container_data, timeline_response):
    # YOUR LOGIC HERE:
    # if container_data['Trade Type'] == 'IMPORT':
    #     if container_data['Status'] == 'FULL':
    #         return 'PICK FULL'
    # etc...
    pass
```

---

### Function 3: `determine_trucking_company(container_data, trucking_companies)`
**Purpose:** Choose which trucking company to use

**You need to tell me:**
- How do you decide between 'K & R TRANSPORTATION LLC' and 'California Cartage Express'?
- Is it based on container data? Always the same? Random? Other logic?

**Example:**
```python
def determine_trucking_company(container_data, trucking_companies):
    # YOUR LOGIC HERE:
    # if some_condition:
    #     return 'K & R TRANSPORTATION LLC'
    # else:
    #     return 'California Cartage Express'
    pass
```

---

### Function 4: `extract_container_info_from_timeline(timeline_response)`
**Purpose:** Extract additional information from timeline (if needed)

**You need to tell me:**
- What information do we need from the timeline?
- Truck plate? Chassis info? Pin code? Other?

---

## Next Steps

**Please provide the logic for each function:**

1. **Terminal determination logic**
2. **Move type determination logic**
3. **Trucking company selection logic**
4. **Timeline extraction logic (if any)**

Once you provide the logic, I'll implement it and the system will be complete!
