import os
import json
import time
import shutil
import logging
from datetime import datetime
import pandas as pd
from services.timeline_utils import extract_milestone_date, find_earliest_appointment

logger = logging.getLogger(__name__)


def get_check(emodal_client, session_id, container_data, query_folder, terminal_mapping, trucking_companies, max_retries=2):
    """
    Complete container appointment checking process (handles IMPORT/EXPORT)
    
    Steps:
    1. Determine terminal from container data
    2. IMPORT: Get timeline → check passed_pregate → determine move_type
       EXPORT: Get booking number → move_type = DROP FULL
    3. Check appointments with derived information
    4. Save response JSON and screenshot
    5. Retry on failure with session recovery if needed
    
    Args:
        emodal_client: EModalClient instance
        session_id: Active E-Modal session
        container_data: Dict with container information from Excel row
        query_folder: Path to query folder for storing results
        terminal_mapping: Dict mapping terminal codes to full names
        trucking_companies: List of available trucking companies
        max_retries: Maximum number of retry attempts (default: 2)
    
    Returns:
        dict: {
            'success': bool,
            'container_number': str,
            'trade_type': str,
            'move_type': str,
            'terminal': str,
            'available_times': list,
            'screenshot_path': str,
            'response_path': str,
            'timestamp': int,
            'error': str (if failed),
            'retries': int (number of retries attempted)
        }
    """
    container_number = str(container_data.get('Container #', '')).strip()
    trade_type = str(container_data.get('Trade Type', '')).strip().upper()
    timestamp = int(time.time())
    
    result = {
        'success': False,
        'container_number': container_number,
        'trade_type': trade_type,
        'timestamp': timestamp,
        'retries': 0
    }
    
    # Retry loop
    for retry_attempt in range(max_retries):
        if retry_attempt > 0:
            logger.info(f"Retry attempt {retry_attempt}/{max_retries-1} for container {container_number}")
            result['retries'] = retry_attempt
            time.sleep(2)  # Brief delay between retries
        
        try:
            # STEP 1: Determine terminal
            terminal = determine_terminal(container_data, terminal_mapping)
            if not terminal:
                result['error'] = 'Could not determine terminal'
                return result
                result['terminal'] = terminal
            
            # STEP 2: Determine trucking company
            trucking_company = determine_trucking_company(container_data, trucking_companies)
            
            # STEP 3: Handle IMPORT vs EXPORT flow
            timeline_response = None
            booking_number = None
            identifier = container_number  # Will be container_number or booking_number
            
            if trade_type == 'IMPORT':
                # IMPORT: Get timeline to check passed_pregate
                logger.info(f"IMPORT flow: Getting timeline for {container_number}")
                timeline_response = emodal_client.get_container_timeline(session_id, container_number)
                
                if not timeline_response.get('success'):
                    result['error'] = 'Timeline fetch failed'
                    raise Exception('Timeline fetch failed')
            else:
                # EXPORT: Get booking number
                logger.info(f"EXPORT flow: Getting booking number for {container_number}")
                booking_response = emodal_client.get_booking_number(session_id, container_number, debug=False)
                
                if not booking_response.get('success') or not booking_response.get('booking_number'):
                    result['error'] = f"Could not get booking number: {booking_response.get('error', 'Unknown error')}"
                    raise Exception(f"Could not get booking number")
                
                booking_number = booking_response.get('booking_number')
                identifier = booking_number  # Use booking number for EXPORT
                result['booking_number'] = booking_number
                logger.info(f"Got booking number: {booking_number}")
            
            # STEP 4: Determine move type
            move_type = determine_move_type(container_data, timeline_response)
            result['move_type'] = move_type
            
            # STEP 5: Check appointments
            logger.info(f"Checking appointments: {identifier}, {terminal}, {move_type}, {trucking_company}")
            appointment_response = emodal_client.check_appointments(
                session_id=session_id,
                trucking_company=trucking_company,
                terminal=terminal,
                move_type=move_type,
                container_id=identifier,  # Container number for IMPORT, booking number for EXPORT
                truck_plate='ABC123',  # Placeholder
                own_chassis=False
                )
            
            # STEP 6: Save response JSON
            response_filename = f"{container_number}_{timestamp}.json"
            response_path = os.path.join(
                query_folder,
                'containers_checking_attempts',
                'responses',
                response_filename
            )
            
            os.makedirs(os.path.dirname(response_path), exist_ok=True)
            
            combined_response = {
                'container_data': container_data,
                'timeline': timeline_response,
                'booking_number': booking_number,
                'appointment_check': appointment_response,
                'terminal': terminal,
                'move_type': move_type,
                'trucking_company': trucking_company,
                'timestamp': timestamp
            }
            
            with open(response_path, 'w') as f:
                json.dump(combined_response, f, indent=2)
            
            result['response_path'] = response_path
            
            # STEP 7: Download and save screenshot
            screenshot_url = appointment_response.get('dropdown_screenshot_url')
            if screenshot_url:
                screenshot_filename = f"{container_number}_{timestamp}.png"
                screenshot_path = os.path.join(
                    query_folder,
                    'containers_checking_attempts',
                    'screenshots',
                    screenshot_filename
                )
                
                emodal_client.download_file(screenshot_url, screenshot_path)
                result['screenshot_path'] = screenshot_path
            
            # STEP 8: Extract results
            result['success'] = appointment_response.get('success', False)
            result['available_times'] = appointment_response.get('available_times', [])
        
            if not result['success']:
                result['error'] = appointment_response.get('error', 'Appointment check failed')
            
            # If successful, break retry loop
            if result['success']:
                break
            
            # If this was not the last retry, log that we'll retry
            if retry_attempt < max_retries - 1:
                logger.warning(f"Container {container_number} check failed, will retry: {result.get('error')}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"get_check attempt {retry_attempt+1} failed for {container_number}: {e}")
            
            # If this was not the last retry, continue to next attempt
            if retry_attempt < max_retries - 1:
                logger.info(f"Will retry container {container_number}")
                continue
    
    return result


def determine_terminal(container_data, terminal_mapping):
    """
    Determine terminal full name from container data
    
    Args:
        container_data: Dict with container information from filtered Excel row
        terminal_mapping: Dict mapping terminal codes to full names
        
    Returns:
        str: Terminal full name for appointment, or None if not found
        
    Logic:
        - IMPORT: Use CurrentLoc (J) if exists, else Origin (H)
        - EXPORT: Use CurrentLoc (J) if exists, else Destination (I)
    """
    trade_type = str(container_data.get('Trade Type', '')).strip().upper()
    current_loc = str(container_data.get('Current Loc', '')).strip()
    origin = str(container_data.get('Origin', '')).strip()
    destination = str(container_data.get('Destination', '')).strip()
    
    # Determine terminal code based on trade type
    if trade_type == 'IMPORT':
        terminal_code = current_loc if current_loc and current_loc != 'nan' else origin
    else:  # EXPORT
        terminal_code = current_loc if current_loc and current_loc != 'nan' else destination
    
    # Map to full terminal name
    terminal_full_name = terminal_mapping.get(terminal_code)
    
    if not terminal_full_name:
        logger.warning(f"Terminal code '{terminal_code}' not found in mapping for {trade_type}")
    else:
        logger.info(f"Terminal determined: {terminal_code} -> {terminal_full_name} ({trade_type})")
    
    return terminal_full_name


def determine_move_type(container_data, timeline_response):
    """
    Determine move type from container data and timeline
    
    Args:
        container_data: Dict with container information from filtered Excel row
        timeline_response: Timeline response from E-Modal API (only for IMPORT)
        
    Returns:
        str: One of 'PICK FULL', 'DROP FULL', 'PICK EMPTY', 'DROP EMPTY'
        
    Logic:
        - IMPORT: Check passed_pregate from timeline
            - If passed_pregate = true → DROP EMPTY
            - If passed_pregate = false → PICK FULL
        - EXPORT: Always DROP FULL
    """
    trade_type = str(container_data.get('Trade Type', '')).strip().upper()
    
    if trade_type == 'IMPORT':
        # Check passed_pregate from timeline response
        passed_pregate = timeline_response.get('passed_pregate', False) if timeline_response else False
        
        if passed_pregate:
            move_type = 'DROP EMPTY'
            logger.info(f"IMPORT with passed_pregate=True -> {move_type}")
        else:
            move_type = 'PICK FULL'
            logger.info(f"IMPORT with passed_pregate=False -> {move_type}")
    else:  # EXPORT
        move_type = 'DROP FULL'
        logger.info(f"EXPORT -> {move_type}")
    
    return move_type


def determine_trucking_company(container_data, trucking_companies):
    """
    Determine which trucking company to use
    
    Args:
        container_data: Dict with container information from filtered Excel row
        trucking_companies: List of available trucking companies
        
    Returns:
        str: Trucking company name
        
    Logic:
        - Use any trucking company (default to first one)
    """
    # Use the first trucking company from the list
    trucking_company = trucking_companies[0] if trucking_companies else 'K & R TRANSPORTATION LLC'
    logger.info(f"Using trucking company: {trucking_company}")
    return trucking_company


def extract_container_info_from_timeline(timeline_response):
    """
    Extract container information from timeline response
    
    Args:
        timeline_response: Timeline response from E-Modal API
        
    Returns:
        dict: Extracted information from timeline (like truck plate, chassis info, etc.)
    """
    # TODO: You will provide the logic for this
    # Extract relevant information from the timeline
    logger.warning("Using placeholder timeline extraction - awaiting logic from user")
    return {
        'truck_plate': 'ABC123',
        'own_chassis': False
    }


class QueryService:
    # Terminal code mappings (code in Excel -> actual terminal name for appointment)
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
        'WUT': 'Washington United Terminals',
        'BNLPC': 'Long Beach Container Terminal',  # Added
        'LPCHI': 'Long Beach Container Terminal - Chicago'  # Added
    }
    
    # Trucking company options
    TRUCKING_COMPANIES = [
        'K & R TRANSPORTATION LLC',
        'California Cartage Express'
    ]
    
    # Move type options
    MOVE_TYPES = [
        'PICK FULL',
        'DROP FULL',
        'PICK EMPTY',
        'DROP EMPTY'
    ]
    
    def __init__(self, emodal_client):
        self.emodal_client = emodal_client
    
    def execute_query(self, user):
        """
        Execute complete query cycle for a user
        
        Returns:
            query_id: str
        """
        from models import db, Query
        
        # Generate query ID
        query_id = f"q_{user.id}_{int(time.time())}"
        
        # Create query record
        query = Query(
            query_id=query_id,
            user_id=user.id,
            platform='emodal',
            status='pending',
            folder_path=self._get_query_folder_path(user.id, query_id)
        )
        db.session.add(query)
        db.session.commit()
        
        # Create folder structure
        from services.file_service import FileService
        FileService.create_query_folders(query.folder_path)
        
        try:
            # Update status to in_progress
            query.status = 'in_progress'
            db.session.commit()
            
            # Ensure user has active session
            session_id = self._ensure_session(user)
            
            # Execute query steps
            summary_stats = self._execute_query_steps(user, query, session_id)
            
            # Mark as completed
            query.status = 'completed'
            query.summary_stats = summary_stats
            query.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Query {query_id} completed successfully")
            
        except Exception as e:
            # Mark as failed
            query.status = 'failed'
            query.error_message = str(e)
            query.completed_at = datetime.utcnow()
            db.session.commit()
            logger.error(f"Query {query_id} failed: {e}")
        
        return query_id
    
    def _ensure_session(self, user):
        """Ensure user has active E-Modal session"""
        from models import db
        from services.file_service import FileService
        
        if user.session_id:
            # TODO: Verify session is still valid
            logger.info(f"Reusing existing session for user {user.username}")
            return user.session_id
        
        # Load credentials
        creds = FileService.load_user_credentials(user)
        emodal_creds = creds.get('emodal', {})
        
        # Create new session
        logger.info(f"Creating new E-Modal session for user {user.username}")
        session_response = self.emodal_client.get_session(
            username=emodal_creds['username'],
            password=emodal_creds['password'],
            captcha_api_key=emodal_creds['captcha_api_key']
        )
        
        if not session_response.get('success'):
            raise Exception("Failed to create E-Modal session")
        
        # Store session ID
        user.session_id = session_response['session_id']
        db.session.commit()
        
        return user.session_id
    
    def _execute_query_steps(self, user, query, session_id):
        """Execute all query steps"""
        start_time = time.time()
        stats = {}
        
        print(f"\n{'='*80}")
        print(f"  STEP 1: GET ALL CONTAINERS")
        print(f"{'='*80}")
        print(f"[QUERY {query.query_id}] Calling E-Modal API: get_containers()")
        print(f"[QUERY {query.query_id}] Session ID: {session_id[:40]}...")
        print(f"[QUERY {query.query_id}] Timeout: 40 minutes")
        logger.info(f"Getting all containers for query {query.query_id}")
        
        # Try to get containers with retry on session error
        max_retries = 2
        for attempt in range(max_retries):
            try:
                containers_response = self.emodal_client.get_containers(session_id)
                
                if containers_response.get('success'):
                    break  # Success, exit retry loop
                
                error_msg = containers_response.get('error', '')
                print(f"[WARNING] Get containers failed: {error_msg}")
                
                # Check if it's a session error (400 Bad Request)
                if '400' in str(error_msg) or 'BAD REQUEST' in str(error_msg).upper():
                    if attempt < max_retries - 1:  # Not last attempt
                        print(f"[INFO] Session appears invalid, creating new session...")
                        session_id = self._recover_session(user)
                        print(f"[INFO] New session created: {session_id[:40]}...")
                        print(f"[INFO] Retrying get_containers...")
                        continue
                
                # Not a session error or last attempt failed
                print(f"[ERROR] Failed to get containers: {error_msg}")
                raise Exception(f"Failed to get containers: {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] Exception getting containers: {error_msg}")
                
                # Check if it's a session error
                if '400' in error_msg or 'BAD REQUEST' in error_msg.upper():
                    if attempt < max_retries - 1:  # Not last attempt
                        print(f"[INFO] Session error detected, recovering...")
                        session_id = self._recover_session(user)
                        print(f"[INFO] New session: {session_id[:40]}...")
                        print(f"[INFO] Retrying...")
                        continue
                
                # Not a session error or last attempt
                raise
        
        print(f"[SUCCESS] Containers retrieved!")
        print(f"[QUERY {query.query_id}] File URL: {containers_response.get('file_url', '')[:50]}...")
        print(f"[QUERY {query.query_id}] Downloading containers file...")
        
        # Download and save containers file
        containers_file = os.path.join(query.folder_path, 'all_containers.xlsx')
        self.emodal_client.download_file(containers_response['file_url'], containers_file)
        print(f"[SUCCESS] Containers file downloaded: {containers_file}")
        
        # Also update master file
        master_containers = os.path.join(user.folder_path, 'emodal', 'all_containers.xlsx')
        os.makedirs(os.path.dirname(master_containers), exist_ok=True)
        shutil.copy(containers_file, master_containers)
        
        stats['total_containers'] = containers_response.get('containers_count', 0)
        print(f"[QUERY {query.query_id}] Total containers: {stats['total_containers']}")
        
        print(f"\n{'='*80}")
        print(f"  STEP 2: FILTER CONTAINERS")
        print(f"{'='*80}")
        print(f"[QUERY {query.query_id}] Reading containers from: {containers_file}")
        print(f"[QUERY {query.query_id}] Filter criteria: Holds=NO AND Pregate contains N/A")
        logger.info(f"Filtering containers for query {query.query_id}")
        
        filtered_df = self._filter_containers(containers_file)
        print(f"[SUCCESS] Filtering complete!")
        print(f"[QUERY {query.query_id}] Filtered: {len(filtered_df)} containers")
        
        # Add new columns (S onwards) for appointment data
        print(f"[QUERY {query.query_id}] Adding appointment tracking columns...")
        filtered_df['Manifested'] = 'N/A'
        filtered_df['First Appointment Available (Before)'] = 'N/A'
        filtered_df['Departed Terminal'] = 'N/A'
        filtered_df['First Appointment Available (After)'] = 'N/A'
        filtered_df['Empty Received'] = 'N/A'
        
        filtered_file = os.path.join(query.folder_path, 'filtered_containers.xlsx')
        filtered_df.to_excel(filtered_file, index=False)
        print(f"[QUERY {query.query_id}] Filtered file saved: {filtered_file}")
        
        stats['filtered_containers'] = len(filtered_df)
        
        # Show breakdown
        import_count = len(filtered_df[filtered_df['Trade Type'].str.upper() == 'IMPORT'])
        export_count = len(filtered_df[filtered_df['Trade Type'].str.upper() == 'EXPORT'])
        print(f"[QUERY {query.query_id}] Breakdown: {import_count} IMPORT, {export_count} EXPORT")
        
        print(f"\n{'='*80}")
        print(f"  STEP 3: GET BULK CONTAINER INFO")
        print(f"{'='*80}")
        print(f"[QUERY {query.query_id}] Calling E-Modal API: get_info_bulk()")
        print(f"[QUERY {query.query_id}] IMPORT containers: {import_count}")
        print(f"[QUERY {query.query_id}] EXPORT containers: {export_count}")
        print(f"[QUERY {query.query_id}] Timeout: 40 minutes")
        print(f"[QUERY {query.query_id}] This may take 1-5 minutes...")
        logger.info(f"Getting bulk info for {len(filtered_df)} containers")
        
        bulk_info = self._get_bulk_container_info(session_id, filtered_df)
        print(f"[SUCCESS] Bulk info retrieved for {len(bulk_info)} containers!")
        
        # Extract timeline milestones from bulk_info and update filtered_df
        print(f"[QUERY {query.query_id}] Extracting timeline milestones...")
        self._extract_timeline_data(filtered_df, bulk_info)
        
        # Save updated filtered file with timeline data
        filtered_df.to_excel(filtered_file, index=False)
        print(f"[QUERY {query.query_id}] Timeline data added to filtered file")
        
        print(f"\n{'='*80}")
        print(f"  STEP 4: CHECK APPOINTMENTS")
        print(f"{'='*80}")
        print(f"[QUERY {query.query_id}] Processing {len(filtered_df)} containers")
        print(f"[QUERY {query.query_id}] EXPORT containers will be skipped")
        print(f"[QUERY {query.query_id}] Expected to process: {import_count} IMPORT containers")
        logger.info(f"Checking appointments for {len(filtered_df)} containers")
        
        check_results = self._check_containers_with_bulk_info(
            session_id,
            filtered_df,
            query.folder_path,
            user,
            bulk_info,
            filtered_file  # Pass filtered file path to update appointment data
        )
        
        print(f"\n[SUCCESS] Container checking complete!")
        print(f"[QUERY {query.query_id}] Results: {check_results}")
        print(f"[QUERY {query.query_id}] Successful: {check_results['success_count']}")
        print(f"[QUERY {query.query_id}] Failed: {check_results['failed_count']}")
        
        stats['checked_containers'] = check_results['success_count']
        stats['failed_checks'] = check_results['failed_count']
        stats['skipped_containers'] = 0  # No longer skipping EXPORT
        
        print(f"\n{'='*80}")
        print(f"  STEP 5: GET ALL APPOINTMENTS")
        print(f"{'='*80}")
        print(f"[QUERY {query.query_id}] Calling E-Modal API: get_appointments()")
        print(f"[QUERY {query.query_id}] Timeout: 40 minutes")
        logger.info(f"Getting all appointments for query {query.query_id}")
        
        # Try to get appointments with retry on session error
        max_retries = 2
        for attempt in range(max_retries):
            try:
                appointments_response = self.emodal_client.get_appointments(session_id)
                
                if appointments_response.get('success'):
                    break  # Success, exit retry loop
                
                error_msg = appointments_response.get('error', '')
                print(f"[WARNING] Get appointments failed: {error_msg}")
                
                # Check if it's a session error (400 Bad Request)
                if '400' in str(error_msg) or 'BAD REQUEST' in str(error_msg).upper():
                    if attempt < max_retries - 1:  # Not last attempt
                        print(f"[INFO] Session appears invalid, creating new session...")
                        session_id = self._recover_session(user)
                        print(f"[INFO] New session created: {session_id[:40]}...")
                        print(f"[INFO] Retrying get_appointments...")
                        continue
                
                # Not a session error or last attempt failed
                print(f"[ERROR] Failed to get appointments: {error_msg}")
                raise Exception(f"Failed to get appointments: {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] Exception getting appointments: {error_msg}")
                
                # Check if it's a session error
                if '400' in error_msg or 'BAD REQUEST' in error_msg.upper():
                    if attempt < max_retries - 1:  # Not last attempt
                        print(f"[INFO] Session error detected, recovering...")
                        session_id = self._recover_session(user)
                        print(f"[INFO] New session: {session_id[:40]}...")
                        print(f"[INFO] Retrying...")
                        continue
                
                # Not a session error or last attempt
                raise
        
        print(f"[SUCCESS] Appointments retrieved!")
        print(f"[QUERY {query.query_id}] File URL: {appointments_response.get('file_url', '')[:50]}...")
        print(f"[QUERY {query.query_id}] Downloading appointments file...")
        
        # Download and save appointments file
        appointments_file = os.path.join(query.folder_path, 'all_appointments.xlsx')
        self.emodal_client.download_file(appointments_response['file_url'], appointments_file)
        print(f"[SUCCESS] Appointments file downloaded: {appointments_file}")
        
        # Also update master file
        master_appointments = os.path.join(user.folder_path, 'emodal', 'all_appointments.xlsx')
        os.makedirs(os.path.dirname(master_appointments), exist_ok=True)
        shutil.copy(appointments_file, master_appointments)
        
        stats['total_appointments'] = appointments_response.get('selected_count', 0)
        stats['duration_seconds'] = int(time.time() - start_time)
        
        print(f"\n{'='*80}")
        print(f"  QUERY COMPLETED SUCCESSFULLY!")
        print(f"{'='*80}")
        print(f"[QUERY {query.query_id}] Total containers: {stats['total_containers']}")
        print(f"[QUERY {query.query_id}] Filtered containers: {stats['filtered_containers']}")
        print(f"[QUERY {query.query_id}] Checked containers: {stats['checked_containers']} (IMPORT + EXPORT)")
        print(f"[QUERY {query.query_id}] Failed checks: {stats['failed_checks']}")
        print(f"[QUERY {query.query_id}] Total appointments: {stats['total_appointments']}")
        print(f"[QUERY {query.query_id}] Duration: {stats['duration_seconds']} seconds ({stats['duration_seconds']//60} minutes)")
        print(f"{'='*80}\n")
        
        logger.info(f"Query {query.query_id} execution completed: {stats}")
        return stats
    
    def _filter_containers(self, containers_file):
        """Filter containers based on Hold and Pregate columns"""
        # Read Excel with keep_default_na=False to preserve "N/A" as strings instead of NaN
        df = pd.read_excel(containers_file, keep_default_na=False)
        
        # Filter logic: 
        # - Column D (Holds) = "NO" (uppercase)
        # - Column E (Pregate Ticket#) is NaN OR contains only asterisks
        # Note: Excel columns are 0-indexed in pandas, so D=3, E=4
        
        try:
            # Try by column position first
            # Holds = "NO" (case-insensitive)
            holds_condition = df.iloc[:, 3].astype(str).str.upper().str.strip() == "NO"
            
            # Pregate contains "N/A" (now properly read as string "N/A" instead of NaN)
            pregate_col = df.iloc[:, 4]
            pregate_condition = (
                pregate_col.astype(str).str.upper().str.contains("N/A", regex=False, na=False)
            )
            
            filtered = df[holds_condition & pregate_condition]
            
            logger.info(f"Filtered by position - Holds='NO' and Pregate contains 'N/A'")
            
        except Exception as e:
            logger.warning(f"Failed to filter by position, trying by column names: {e}")
            # Fallback to column names if they exist
            try:
                holds_condition = df['Holds'].astype(str).str.upper().str.strip() == "NO"
                pregate_col = df['Pregate Ticket#']
                pregate_condition = (
                    pregate_col.astype(str).str.upper().str.contains("N/A", regex=False, na=False)
                )
                filtered = df[holds_condition & pregate_condition]
                logger.info(f"Filtered by column names - Holds='NO' and Pregate contains 'N/A'")
            except Exception as e2:
                logger.error(f"Failed to filter containers: {e2}")
                # Return empty DataFrame if filtering fails
                filtered = df.iloc[0:0]
        
        logger.info(f"Filtered {len(filtered)} containers from {len(df)} total")
        return filtered
    
    def _get_bulk_container_info(self, session_id, filtered_df):
        """
        Get bulk container information (pregate status for IMPORT, booking numbers for EXPORT)
        
        Args:
            session_id: Active session ID
            filtered_df: DataFrame with filtered containers
            
        Returns:
            dict: Bulk information results indexed by container number
        """
        # Separate containers by trade type
        import_containers = []
        export_containers = []
        
        for idx, row in filtered_df.iterrows():
            container_num = str(row['Container #']).strip()
            trade_type = str(row['Trade Type']).strip().upper()
            
            if trade_type == 'IMPORT':
                import_containers.append(container_num)
            elif trade_type == 'EXPORT':
                export_containers.append(container_num)
        
        logger.info(f"Bulk request: {len(import_containers)} IMPORT, {len(export_containers)} EXPORT containers")
        
        # Call bulk endpoint
        print(f"\n>>> Calling E-Modal API: POST /get_info_bulk")
        print(f">>> IMPORT containers: {import_containers}")
        print(f">>> EXPORT containers: {export_containers}")
        print(f">>> Waiting for response (timeout: 30 minutes)...")
        
        bulk_response = self.emodal_client.get_info_bulk(
            session_id=session_id,
            import_containers=import_containers,
            export_containers=export_containers,
            debug=False
        )
        
        print(f">>> Bulk API response received!")
        
        if not bulk_response.get('success'):
            logger.error(f"Bulk info request failed: {bulk_response.get('error')}")
            return {}
        
        # Build lookup dict: container_number -> info
        bulk_info = {}
        
        # Process import results (now includes full timeline)
        for result in bulk_response.get('results', {}).get('import_results', []):
            container_id = result.get('container_id')
            bulk_info[container_id] = {
                'trade_type': 'IMPORT',
                'success': result.get('success', False),
                'pregate_status': result.get('pregate_status'),
                'pregate_details': result.get('pregate_details', ''),
                'timeline': result.get('timeline', []),  # NEW: Full timeline data
                'milestone_count': result.get('milestone_count', 0),
                'error': result.get('error')
            }
        
        # Process export results
        for result in bulk_response.get('results', {}).get('export_results', []):
            container_id = result.get('container_id')
            bulk_info[container_id] = {
                'trade_type': 'EXPORT',
                'success': result.get('success', False),
                'booking_number': result.get('booking_number'),
                'error': result.get('error')
            }
        
        logger.info(f"Bulk info retrieved for {len(bulk_info)} containers")
        return bulk_info
    
    def _check_containers_with_bulk_info(self, session_id, filtered_df, query_folder, user, bulk_info, filtered_file):
        """
        Check appointments for containers using pre-fetched bulk information and update Excel
        
        Args:
            session_id: Active session ID
            filtered_df: DataFrame with filtered containers
            query_folder: Query folder path
            filtered_file: Path to filtered Excel file for updates
            user: User object
            bulk_info: Dict with pre-fetched pregate/booking info
        """
        success_count = 0
        failed_containers = []
        skipped_containers = []
        processed_containers = []
        
        # Check for existing progress
        progress_file = os.path.join(query_folder, 'check_progress.json')
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress = json.load(f)
                processed_containers = progress.get('processed', [])
                logger.info(f"Resuming from previous run - {len(processed_containers)} already processed")
        
        logger.info(f"Checking {len(filtered_df)} containers ({len(processed_containers)} already done)")
        
        for idx, row in filtered_df.iterrows():
            container_data = row.to_dict()
            container_num = str(container_data.get('Container #', '')).strip()
            trade_type = str(container_data.get('Trade Type', '')).strip().upper()
            
            # Skip if already processed
            if container_num in processed_containers:
                logger.info(f"Skipping already processed container: {container_num}")
                continue
            
            # EXPORT containers are now processed (no longer skipped)
            # They use booking_number instead of container_id
            
            # Get bulk info for this container
            info = bulk_info.get(container_num, {})
            if not info or not info.get('success'):
                logger.warning(f"No bulk info for {container_num}, skipping")
                failed_containers.append(container_num)
                processed_containers.append(container_num)
                self._save_progress(progress_file, processed_containers)
                continue
            
            print(f"\n[{idx+1}/{len(filtered_df)}] Processing container: {container_num} ({trade_type})")
            logger.info(f"Checking container {idx+1}/{len(filtered_df)}: {container_num} ({trade_type})")
            print(f"  > Pregate status from bulk: {info.get('pregate_status')}")
            logger.info(f"  Pregate status from bulk: {info.get('pregate_status')}")
            
            # Determine terminal
            print(f"  > Determining terminal...")
            terminal = determine_terminal(container_data, self.TERMINAL_MAPPING)
            if not terminal:
                logger.warning(f"Could not determine terminal for {container_num}")
                failed_containers.append(container_num)
                processed_containers.append(container_num)
                self._save_progress(progress_file, processed_containers)
                continue
            
            # Determine trucking company
            trucking_company = determine_trucking_company(container_data, self.TRUCKING_COMPANIES)
            
            # Determine move type using bulk pregate status
            mock_timeline = {
                'success': True,
                'passed_pregate': info.get('pregate_status', False)
            }
            move_type = determine_move_type(container_data, mock_timeline)
            
            print(f"  > Terminal: {terminal}")
            print(f"  > Move Type: {move_type}")
            print(f"  > Trucking: {trucking_company}")
            logger.info(f"  Terminal: {terminal}, Move Type: {move_type}, Trucking: {trucking_company}")
            
            # Check appointments with session retry
            print(f"  > Calling check_appointments API...")
            print(f"  > Container type: {trade_type}")
            
            # Prepare request based on container type
            if trade_type == 'EXPORT':
                # EXPORT: needs booking_number from bulk_info
                booking_number = info.get('booking_number')
                if not booking_number:
                    print(f"  > [ERROR] No booking number found in bulk_info for EXPORT container")
                    failed_containers.append(container_num)
                    processed_containers.append(container_num)
                    self._save_progress(progress_file, processed_containers)
                    continue
                print(f"  > Booking number: {booking_number}")
            
            appointment_response = None
            max_check_retries = 2
            
            for check_attempt in range(max_check_retries):
                try:
                    # Build request parameters based on container type
                    check_params = {
                        'session_id': session_id,
                        'container_type': trade_type.lower(),  # 'import' or 'export'
                        'trucking_company': trucking_company,
                        'terminal': terminal,
                        'move_type': move_type,
                        'truck_plate': 'ABC123',
                        'own_chassis': False,
                        'container_number': container_num  # For screenshot annotation
                    }
                    
                    # Add type-specific parameters
                    if trade_type == 'IMPORT':
                        check_params['container_id'] = container_num
                    else:  # EXPORT
                        check_params['container_id'] = container_num  # Container number
                        check_params['booking_number'] = booking_number  # Booking number
                    
                    appointment_response = self.emodal_client.check_appointments(**check_params)
                    # Success - exit retry loop
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"  > [ERROR] {error_msg}")
                    
                    # Check if it's a session error (400 Bad Request)
                    if ('400' in error_msg or 'BAD REQUEST' in error_msg.upper()) and check_attempt < max_check_retries - 1:
                        print(f"  > [SESSION ERROR] Recovering session...")
                        new_session_id = self._recover_session(user)
                        if new_session_id:
                            session_id = new_session_id
                            print(f"  > [RETRY] Retrying with new session for {container_num}...")
                            continue  # Retry
                    
                    # Not a session error or last attempt - log and skip
                    logger.error(f"Failed to check appointments for {container_num}: {e}")
                    break  # Exit retry loop
            
            try:
                
                # Check if we got a response
                if not appointment_response:
                    print(f"  > [FAILED] No response received after retries")
                    failed_containers.append(container_num)
                    processed_containers.append(container_num)
                    self._save_progress(progress_file, processed_containers)
                    continue
                
                # Save response
                timestamp = int(time.time())
                response_path = os.path.join(
                    query_folder,
                    'containers_checking_attempts',
                    'responses',
                    f"{container_num}_{timestamp}.json"
                )
                os.makedirs(os.path.dirname(response_path), exist_ok=True)
                
                with open(response_path, 'w') as f:
                    json.dump({
                        'container_data': container_data,
                        'bulk_info': info,
                        'appointment_check': appointment_response,
                        'terminal': terminal,
                        'move_type': move_type,
                        'trucking_company': trucking_company,
                        'timestamp': timestamp
                    }, f, indent=2)
                
                # Download screenshot based on container type
                if trade_type == 'IMPORT':
                    screenshot_url = appointment_response.get('dropdown_screenshot_url')
                else:  # EXPORT
                    screenshot_url = appointment_response.get('calendar_screenshot_url')
                
                if screenshot_url:
                    screenshot_path = os.path.join(
                        query_folder,
                        'containers_checking_attempts',
                        'screenshots',
                        f"{container_num}_{timestamp}.png"
                    )
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    self.emodal_client.download_file(screenshot_url, screenshot_path)
                    print(f"  > Screenshot saved: {screenshot_path}")
                
                if appointment_response.get('success'):
                    success_count += 1
                    
                    # Different success criteria for IMPORT vs EXPORT
                    if trade_type == 'IMPORT':
                        slots = len(appointment_response.get('available_times', []))
                        print(f"  > [SUCCESS] Appointments checked - {slots} available slots")
                        logger.info(f"Container {container_num} (IMPORT) check successful - {slots} slots")
                        
                        # Extract and update appointment dates in filtered_df
                        self._update_appointment_dates(
                            filtered_df, 
                            container_num, 
                            appointment_response.get('available_times', []),
                            move_type
                        )
                    else:  # EXPORT
                        calendar_found = appointment_response.get('calendar_found', False)
                        if calendar_found:
                            print(f"  > [SUCCESS] Calendar available for booking")
                            logger.info(f"Container {container_num} (EXPORT) check successful - calendar available")
                        else:
                            print(f"  > [WARNING] Calendar not found")
                            logger.warning(f"Container {container_num} (EXPORT) - calendar not found")
                else:
                    failed_containers.append(container_num)
                    print(f"  > [FAILED] {appointment_response.get('error')}")
                    logger.warning(f"Container {container_num} check failed: {appointment_response.get('error')}")
                
            except Exception as e:
                failed_containers.append(container_num)
                logger.error(f"Failed to check appointments for {container_num}: {e}")
            
            # Mark as processed
            processed_containers.append(container_num)
            self._save_progress(progress_file, processed_containers)
            
            # Save progress to filtered Excel file every 5 containers
            if len(processed_containers) % 5 == 0:
                try:
                    filtered_df.to_excel(filtered_file, index=False)
                    print(f"  > Progress saved: {len(processed_containers)}/{len(filtered_df)} containers")
                except Exception as e:
                    logger.error(f"Failed to save progress to Excel: {e}")
        
        # Final save to filtered Excel file
        try:
            filtered_df.to_excel(filtered_file, index=False)
            print(f"[SUCCESS] Final data saved to filtered Excel file")
        except Exception as e:
            logger.error(f"Failed to save final data to Excel: {e}")
        
        logger.info(f"Check summary: {success_count} successful, {len(failed_containers)} failed")
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_containers),
            'skipped_count': 0  # No longer skipping EXPORT
        }
    
    def _save_progress(self, progress_file, processed_containers):
        """Save progress to file for resume capability"""
        try:
            os.makedirs(os.path.dirname(progress_file), exist_ok=True)
            with open(progress_file, 'w') as f:
                json.dump({
                    'processed': processed_containers,
                    'last_updated': time.time()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def _is_session_error(self, error_msg):
        """Check if error indicates session expiration"""
        session_errors = [
            '400 Client Error: BAD REQUEST',
            '401',
            'Unauthorized',
            'Invalid session',
            'Session expired'
        ]
        return any(err in str(error_msg) for err in session_errors)
    
    def _recover_session(self, user):
        """Create new session when current one expires"""
        try:
            logger.info(f"Attempting to recover session for user {user.username}")
            
            # Load credentials
            cred_file = os.path.join(user.folder_path, 'user_cre_env.json')
            with open(cred_file, 'r') as f:
                creds = json.load(f)
            
            emodal_creds = creds.get('emodal', {})
            
            # Create new session
            session_response = self.emodal_client.get_session(
                username=emodal_creds['username'],
                password=emodal_creds['password'],
                captcha_api_key=emodal_creds['captcha_api_key']
            )
            
            if session_response.get('success') and session_response.get('session_id'):
                new_session_id = session_response['session_id']
                logger.info(f"New session created: {new_session_id[:30]}...")
                
                # Update user's session in database
                from models import db
                user.session_id = new_session_id
                db.session.commit()
                
                return new_session_id
            else:
                logger.error(f"Failed to create new session: {session_response.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Session recovery failed: {e}")
            return None
    
    def _extract_timeline_data(self, filtered_df, bulk_info):
        """Extract timeline milestones from bulk_info and update filtered_df"""
        for idx, row in filtered_df.iterrows():
            container_num = str(row.get('Container', '')).strip()
            trade_type = str(row.get('Trade Type', '')).strip().upper()
            
            # Only process IMPORT containers (EXPORT get N/A)
            if trade_type == 'IMPORT':
                info = bulk_info.get(container_num, {})
                timeline = info.get('timeline', [])
                
                if timeline and isinstance(timeline, list):
                    # Extract milestone dates
                    manifested = extract_milestone_date(timeline, 'Manifested')
                    departed_terminal = extract_milestone_date(timeline, 'Departed Terminal')
                    empty_received = extract_milestone_date(timeline, 'Empty Received')
                    
                    # Update DataFrame
                    filtered_df.at[idx, 'Manifested'] = manifested
                    filtered_df.at[idx, 'Departed Terminal'] = departed_terminal
                    filtered_df.at[idx, 'Empty Received'] = empty_received
                    
                    logger.debug(f"Timeline data for {container_num}: Manifested={manifested}, "
                               f"Departed={departed_terminal}, Empty={empty_received}")
    
    def _update_appointment_dates(self, filtered_df, container_num, available_times, move_type):
        """Update appointment dates in filtered_df based on move type"""
        if not available_times or len(available_times) == 0:
            return
        
        # Find the earliest appointment date
        earliest_date = find_earliest_appointment(available_times)
        
        if earliest_date == 'N/A':
            return
        
        # Find the row for this container
        container_mask = filtered_df['Container'].astype(str).str.strip() == container_num
        
        # Update based on move type
        if move_type == 'PICK FULL':
            filtered_df.loc[container_mask, 'First Appointment Available (Before)'] = earliest_date
            logger.debug(f"Updated appointment (BEFORE) for {container_num}: {earliest_date}")
        elif move_type == 'DROP EMPTY':
            filtered_df.loc[container_mask, 'First Appointment Available (After)'] = earliest_date
            logger.debug(f"Updated appointment (AFTER) for {container_num}: {earliest_date}")
    
    def _get_query_folder_path(self, user_id, query_id):
        """Generate query folder path"""
        return os.path.join(
            'storage', 'users', str(user_id), 'emodal', 'queries', query_id
        )

