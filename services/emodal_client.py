import requests
import os
import logging
import threading
import json

logger = logging.getLogger(__name__)

class EModalClient:
    """
    E-Modal API Client with request serialization.
    Ensures only one API call is made at a time per client instance.
    Updates session before each request.
    """
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self._lock = threading.Lock()  # Ensure sequential API calls
    
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
    
    def get_session(self, username, password, captcha_api_key):
        """Create persistent session with E-Modal"""
        with self._lock:  # Ensure only one session creation at a time
            try:
                logger.info(f"Creating E-Modal session for user: {username}")
                response = self.session.post(f"{self.base_url}/get_session", json={
                    'username': username,
                    'password': password,
                    'captcha_api_key': captcha_api_key
                }, timeout=600)  # 10 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.info(f"E-Modal session created successfully")
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
                }, timeout=600)  # 10 minutes timeout
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
                }, timeout=600)  # 10 minutes timeout
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
    
    def check_appointments(self, session_id, trucking_company, terminal, 
                          move_type, container_id, truck_plate, own_chassis):
        """Check appointment availability"""
        with self._lock:  # Ensure sequential execution
            try:
                # Update session before request
                self.update_session(session_id)
                
                logger.debug(f"Checking appointments for container: {container_id}")
                response = self.session.post(f"{self.base_url}/check_appointments", json={
                    'session_id': session_id,
                    'trucking_company': trucking_company,
                    'terminal': terminal,
                    'move_type': move_type,
                    'container_id': container_id,
                    'truck_plate': truck_plate,
                    'own_chassis': own_chassis,
                    'debug': True
                }, timeout=600)  # 10 minutes timeout
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    result = response.json()
                    logger.debug(f"Appointment check completed for container: {container_id}")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from check_appointments: {response.text[:200]}")
                    raise Exception(f"Invalid JSON from E-Modal API: {response.text[:100]}")
                    
            except Exception as e:
                logger.error(f"Failed to check appointments for {container_id}: {e}")
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
                }, timeout=600)  # 10 minutes timeout
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
                response = self.session.get(url, stream=True, timeout=600)  # 10 minutes timeout
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
                
                response = self.session.post(url, json=payload, timeout=600)  # 10 minutes timeout
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

