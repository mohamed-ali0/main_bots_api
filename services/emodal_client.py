import requests
import os
import logging
import threading
import json
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class TCPKeepAliveAdapter(HTTPAdapter):
    """HTTPAdapter with TCP keep-alive to prevent connection drops during long requests"""
    def init_poolmanager(self, *args, **kwargs):
        # Enable TCP keep-alive (works on Windows, Linux, Mac)
        kwargs['socket_options'] = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
        return super().init_poolmanager(*args, **kwargs)

class EModalClient:
    """
    E-Modal API Client with request serialization.
    Ensures only one API call is made at a time per client instance.
    Updates session before each request.
    """
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Add TCP keep-alive adapter to prevent timeouts on long requests
        adapter = TCPKeepAliveAdapter(max_retries=Retry(total=0))
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self._lock = threading.Lock()  # Ensure sequential API calls
        logger.info(f"E-Modal API client initialized with TCP keep-alive: {base_url}")
        print(f"[SYSTEM] E-Modal client configured for long requests (TCP keep-alive enabled)")
    
    def update_session(self, session_id):
        """
        No-op function - sessions are automatically kept alive for 10 minutes.
        
        According to the API documentation:
        - Sessions are kept alive for 10 minutes of inactivity automatically
        - No explicit update/refresh endpoint needed
        - Simply reusing the session_id keeps it active
        
        Args:
            session_id: Current session ID
            
        Returns:
            dict: Success response (no actual API call needed)
        """
        # No API call needed - sessions auto-refresh on use
        logger.debug(f"Session {session_id[:30]}... will be kept alive automatically")
        return {'success': True, 'message': 'Session auto-refresh enabled'}
    
    def list_active_sessions(self):
        """List all active sessions on the E-Modal API server"""
        try:
            logger.info("Checking for active sessions")
            url = f"{self.base_url}/sessions"
            response = self.session.get(url, timeout=2400)  # 40 minutes timeout
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Found {data.get('active_sessions', 0)} active sessions")
            return data
        except Exception as e:
            logger.warning(f"Failed to list active sessions: {e}")
            return {'active_sessions': 0, 'sessions': []}
    
    def find_active_session_for_user(self, username):
        """Find an active session for a specific username"""
        try:
            sessions_data = self.list_active_sessions()
            
            for session in sessions_data.get('sessions', []):
                if session.get('username') == username:
                    session_id = session.get('session_id')
                    logger.info(f"Found active session for {username}: {session_id[:40]}...")
                    return session_id
            
            logger.info(f"No active session found for {username}")
            return None
        except Exception as e:
            logger.error(f"Failed to find active session: {e}")
            return None
    
    def get_session(self, username, password, captcha_api_key):
        """Get session - checks for active sessions first, creates new if needed"""
        with self._lock:  # Ensure only one session creation at a time
            try:
                # STEP 1: Check for existing active session first
                logger.info(f"Checking for active session for user: {username}")
                active_session_id = self.find_active_session_for_user(username)
                
                if active_session_id:
                    logger.info(f"Reusing active session: {active_session_id[:40]}...")
                    return {
                        'success': True,
                        'session_id': active_session_id,
                        'is_new': False,
                        'username': username,
                        'message': 'Using existing active session from server'
                    }
                
                # STEP 2: No active session found, create new one
                logger.info(f"No active session found, creating new session for: {username}")
                response = self.session.post(f"{self.base_url}/get_session", json={
                    'username': username,
                    'password': password,
                    'captcha_api_key': captcha_api_key
                }, timeout=2400)  # 40 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.info(f"Session created: {result.get('session_id', '')[:40]}... (is_new: {result.get('is_new')})")
                    return result
                except json.JSONDecodeError as je:
                    logger.error(f"Invalid JSON response from get_session: {response.text[:200]}")
                    raise Exception(f"Invalid JSON from E-Modal API: {response.text[:100]}")
                    
            except Exception as e:
                logger.error(f"Failed to get E-Modal session: {e}")
                raise
    
    def get_containers(self, session_id):
        """Get all containers with infinite scrolling"""
        with self._lock:  # Ensure sequential execution
            try:
                # Update session before request
                self.update_session(session_id)
                
                logger.info(f"Getting containers for session: {session_id}")
                response = self.session.post(f"{self.base_url}/get_containers", json={
                    'session_id': session_id,
                    'infinite_scrolling': True,
                    'debug': False,
                    'return_url': True  # Get JSON response with file URL instead of direct file
                }, timeout=2400)  # 40 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.info(f"Containers retrieved successfully. Count: {result.get('total_containers', 'N/A')}")
                    return result
                except json.JSONDecodeError as je:
                    logger.error(f"Invalid JSON response from get_containers. Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
                    raise Exception(f"Expected JSON response but got file. Use return_url=true parameter.")
                    
            except Exception as e:
                logger.error(f"Failed to get containers: {e}")
                raise
    
    def get_container_timeline(self, session_id, container_id):
        """Get timeline for specific container"""
        with self._lock:  # Ensure sequential execution
            try:
                # Update session before request
                self.update_session(session_id)
                
                logger.debug(f"Getting timeline for container: {container_id}")
                response = self.session.post(f"{self.base_url}/get_container_timeline", json={
                    'session_id': session_id,
                    'container_id': container_id,
                    'debug': True
                }, timeout=2400)  # 40 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.debug(f"Timeline retrieved for container: {container_id}")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from get_container_timeline: {response.text[:200]}")
                    raise Exception(f"Invalid JSON from E-Modal API: {response.text[:100]}")
                    
            except Exception as e:
                logger.error(f"Failed to get container timeline for {container_id}: {e}")
                raise
    
    def check_appointments(self, session_id, container_type, trucking_company, terminal, move_type,
                          container_id=None, booking_number=None, truck_plate='ABC123', own_chassis=False,
                          container_number=None, pin_code=None, unit_number=None, seal_value=None,
                          manifested_date=None, departed_date=None):
        """Check appointment availability for IMPORT or EXPORT containers"""
        with self._lock:  # Ensure sequential execution
            try:
                # Update session before request
                self.update_session(session_id)
                
                # Build payload
                payload = {
                    'session_id': session_id,
                    'container_type': container_type,
                    'trucking_company': trucking_company,
                    'terminal': terminal,
                    'move_type': move_type,
                    'truck_plate': truck_plate,
                    'debug': True
                }
                
                # Add all optional fields
                if container_number:
                    payload['container_number'] = container_number
                if container_id:
                    payload['container_id'] = container_id
                if booking_number:
                    payload['booking_number'] = booking_number
                if pin_code:
                    payload['pin_code'] = pin_code
                if unit_number:
                    payload['unit_number'] = unit_number
                if seal_value:
                    payload['seal_value'] = seal_value
                if manifested_date:
                    payload['manifested_date'] = manifested_date
                if departed_date:
                    payload['departed_date'] = departed_date
                
                logger.debug(f"Checking appointments for {container_type.upper()}: {container_id or booking_number}")
                response = self.session.post(f"{self.base_url}/check_appointments", json=payload, timeout=2400)
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.debug(f"Appointment check completed for {container_type.upper()}")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from check_appointments: {response.text[:200]}")
                    raise Exception(f"Invalid JSON from E-Modal API: {response.text[:100]}")
                    
            except Exception as e:
                logger.error(f"Failed to check appointments: {e}")
                raise
    
    def get_appointments(self, session_id):
        """Get all appointments with infinite scrolling"""
        with self._lock:  # Ensure sequential execution
            try:
                # Update session before request
                self.update_session(session_id)
                
                logger.info(f"Getting appointments for session: {session_id}")
                response = self.session.post(f"{self.base_url}/get_appointments", json={
                    'session_id': session_id,
                    'infinite_scrolling': True,
                    'debug': False,
                    'return_url': True  # Get JSON response with file URL instead of direct file
                }, timeout=2400)  # 40 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.info(f"Appointments retrieved successfully. Count: {result.get('selected_count', 'N/A')}")
                    return result
                except json.JSONDecodeError as je:
                    logger.error(f"Invalid JSON response from get_appointments. Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
                    raise Exception(f"Expected JSON response but got file. Use return_url=true parameter.")
                    
            except Exception as e:
                logger.error(f"Failed to get appointments: {e}")
                raise
    
    def download_file(self, url, destination_path):
        """Download file from URL"""
        with self._lock:  # Ensure sequential execution
            try:
                logger.debug(f"Downloading file from: {url}")
                response = self.session.get(url, stream=True, timeout=2400)  # 40 minutes timeout
                response.raise_for_status()
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(destination_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Downloaded file to {destination_path}")
            except Exception as e:
                logger.error(f"Failed to download file from {url}: {e}")
                raise
    
    def get_booking_number(self, session_id, container_id, debug=False):
        """
        Get booking number for a container (EXPORT containers)
        
        Args:
            session_id: Browser session ID
            container_id: Container number
            debug: Whether to enable debug mode
            
        Returns:
            dict: Response with booking_number or error
        """
        with self._lock:  # Ensure sequential execution
            try:
                logger.info(f"Getting booking number for container: {container_id}")
                
                # Update session before calling
                self.update_session(session_id)
                
                url = f"{self.base_url}/get_booking_number"
                payload = {
                    'session_id': session_id,
                    'container_id': container_id,
                    'debug': debug
                }
                
                response = self.session.post(url, json=payload, timeout=2400)  # 40 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    data = response.json()
                    logger.info(f"Booking number response: success={data.get('success')}, booking={data.get('booking_number')}")
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse booking number response as JSON: {e}")
                    logger.error(f"Response Content-Type: {response.headers.get('Content-Type')}")
                    logger.error(f"Response text (first 200 chars): {response.text[:200]}")
                    raise Exception(f"Invalid JSON response: {str(e)}")
                
            except Exception as e:
                logger.error(f"Get booking number failed: {e}")
                raise
    
    def get_info_bulk(self, session_id, import_containers=None, export_containers=None, debug=False):
        """
        Get bulk container information (pregate status for IMPORT, booking numbers for EXPORT)
        
        Args:
            session_id: Browser session ID
            import_containers: List of import container IDs
            export_containers: List of export container IDs
            debug: Whether to enable debug mode
            
        Returns:
            dict: Response with import_results and export_results
        """
        with self._lock:  # Ensure sequential execution
            try:
                logger.info(f"Getting bulk info: {len(import_containers or [])} IMPORT, {len(export_containers or [])} EXPORT")
                
                url = f"{self.base_url}/get_info_bulk"
                payload = {
                    'session_id': session_id,
                    'import_containers': import_containers or [],
                    'export_containers': export_containers or [],
                    'debug': debug
                }
                
                print(f">>> Sending request to: {url}")
                print(f">>> Payload: import={len(payload['import_containers'])}, export={len(payload['export_containers'])}")
                print(f">>> Waiting for response (timeout: 40 minutes, typically 1-5 minutes)...")
                print(f">>> REQUEST SENT at {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")
                print(f">>> E-Modal API is processing... (progress indicator will print every 30 seconds)")
                
                import time
                import threading as thread_module
                start_time = time.time()
                
                # Progress indicator thread
                stop_indicator = thread_module.Event()
                def print_progress():
                    count = 0
                    while not stop_indicator.is_set():
                        time.sleep(30)
                        if not stop_indicator.is_set():
                            count += 30
                            elapsed_min = count // 60
                            elapsed_sec = count % 60
                            print(f">>> Still waiting... ({elapsed_min}m {elapsed_sec}s elapsed)")
                
                progress_thread = thread_module.Thread(target=print_progress, daemon=True)
                progress_thread.start()
                
                try:
                    response = self.session.post(url, json=payload, timeout=2400)  # 40 minutes timeout
                finally:
                    stop_indicator.set()
                    
                elapsed = time.time() - start_time
                
                print(f">>> Response received after {elapsed:.1f} seconds!")
                print(f">>> Status code: {response.status_code}")
                print(f">>> Content length: {len(response.content)} bytes")
                print(f">>> Content type: {response.headers.get('content-type', 'unknown')}")
                response.raise_for_status()
                
                # Parse JSON response
                print(f">>> Attempting to parse JSON response...")
                try:
                    print(f">>> Calling response.json()...")
                    data = response.json()
                    print(f">>> JSON parsed successfully!")
                    print(f">>> Response success: {data.get('success')}")
                    logger.info(f"Bulk info response: success={data.get('success')}")
                    if data.get('success'):
                        summary = data.get('results', {}).get('summary', {})
                        print(f">>> Bulk summary: {summary}")
                        logger.info(f"Bulk summary: {summary}")
                    else:
                        print(f">>> Bulk error: {data.get('error', 'Unknown')}")
                    return data
                except json.JSONDecodeError as e:
                    print(f">>> [ERROR] JSON parsing failed!")
                    logger.error(f"Failed to parse bulk info response as JSON: {e}")
                    logger.error(f"Response Content-Type: {response.headers.get('Content-Type')}")
                    logger.error(f"Response text (first 200 chars): {response.text[:200]}")
                    raise Exception(f"Invalid JSON response: {str(e)}")
                
            except Exception as e:
                print(f">>> [EXCEPTION] Bulk API call failed!")
                print(f">>> Exception type: {type(e).__name__}")
                print(f">>> Exception message: {e}")
                logger.error(f"Get bulk info failed: {e}")
                import traceback
                traceback.print_exc()
                raise

