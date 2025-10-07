import os
import json
import time
import shutil
import logging
from datetime import datetime
import pandas as pd

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
        
        # STEP 1: Get all containers
        logger.info(f"Getting all containers for query {query.query_id}")
        containers_response = self.emodal_client.get_containers(session_id)
        if not containers_response.get('success'):
            raise Exception("Failed to get containers")
        
        # Download and save containers file
        containers_file = os.path.join(query.folder_path, 'all_containers.xlsx')
        self.emodal_client.download_file(containers_response['file_url'], containers_file)
        
        # Also update master file
        master_containers = os.path.join(user.folder_path, 'emodal', 'all_containers.xlsx')
        os.makedirs(os.path.dirname(master_containers), exist_ok=True)
        shutil.copy(containers_file, master_containers)
        
        stats['total_containers'] = containers_response.get('containers_count', 0)
        
        # STEP 2: Filter containers
        logger.info(f"Filtering containers for query {query.query_id}")
        filtered_df = self._filter_containers(containers_file)
        filtered_file = os.path.join(query.folder_path, 'filtered_containers.xlsx')
        filtered_df.to_excel(filtered_file, index=False)
        
        stats['filtered_containers'] = len(filtered_df)
        
        # STEP 3: Check each container
        logger.info(f"Checking {len(filtered_df)} containers for query {query.query_id}")
        check_results = self._check_containers(
            session_id,
            filtered_df,
            query.folder_path,
            user
        )
        
        stats['checked_containers'] = check_results['success_count']
        stats['failed_checks'] = check_results['failed_count']
        
        # STEP 4: Get all appointments
        logger.info(f"Getting all appointments for query {query.query_id}")
        appointments_response = self.emodal_client.get_appointments(session_id)
        if not appointments_response.get('success'):
            raise Exception("Failed to get appointments")
        
        # Download and save appointments file
        appointments_file = os.path.join(query.folder_path, 'all_appointments.xlsx')
        self.emodal_client.download_file(appointments_response['file_url'], appointments_file)
        
        # Also update master file
        master_appointments = os.path.join(user.folder_path, 'emodal', 'all_appointments.xlsx')
        os.makedirs(os.path.dirname(master_appointments), exist_ok=True)
        shutil.copy(appointments_file, master_appointments)
        
        stats['total_appointments'] = appointments_response.get('selected_count', 0)
        stats['duration_seconds'] = int(time.time() - start_time)
        
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
    
    def _check_containers(self, session_id, filtered_df, query_folder, user):
        """Check each filtered container sequentially with retry and session recovery"""
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
            
            # Skip EXPORT containers for now
            if trade_type == 'EXPORT':
                logger.info(f"Skipping EXPORT container: {container_num}")
                skipped_containers.append(container_num)
                processed_containers.append(container_num)
                self._save_progress(progress_file, processed_containers)
                continue
            
            logger.info(f"Checking container {idx+1}/{len(filtered_df)}: {container_num} ({trade_type})")
            
            # Check with retry logic (max_retries=3 includes initial attempt)
            result = get_check(
                self.emodal_client,
                session_id,
                container_data,
                query_folder,
                self.TERMINAL_MAPPING,
                self.TRUCKING_COMPANIES,
                max_retries=3
            )
            
            # Check if session expired (400/401 errors)
            if not result['success'] and self._is_session_error(result.get('error', '')):
                logger.warning(f"Session error detected, creating new session")
                session_id = self._recover_session(user)
                if session_id:
                    # Retry with new session
                    logger.info(f"Retrying with new session for {container_num}")
                    result = get_check(
                        self.emodal_client,
                        session_id,
                        container_data,
                        query_folder,
                        self.TERMINAL_MAPPING,
                        self.TRUCKING_COMPANIES,
                        max_retries=2
                    )
            
            if result['success']:
                success_count += 1
            else:
                failed_containers.append(container_num)
                logger.warning(f"Container {container_num} check failed: {result.get('error')}")
            
            # Mark as processed
            processed_containers.append(container_num)
            self._save_progress(progress_file, processed_containers)
        
        logger.info(f"Check summary: {success_count} successful, {len(failed_containers)} failed, {len(skipped_containers)} skipped (EXPORT)")
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_containers),
            'skipped_count': len(skipped_containers)
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
    
    def _get_query_folder_path(self, user_id, query_id):
        """Generate query folder path"""
        return os.path.join(
            'storage', 'users', str(user_id), 'emodal', 'queries', query_id
        )

