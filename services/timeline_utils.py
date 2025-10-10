"""
Timeline and Appointment Data Extraction Utilities
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_milestone_date(timeline, milestone_name):
    """
    Extract date from timeline for a specific milestone
    
    Args:
        timeline: List of milestone dictionaries
        milestone_name: Name of milestone to find
        
    Returns:
        Date string (MM/DD/YYYY) or 'Not Found' if not found or invalid
    """
    if not timeline or not isinstance(timeline, list):
        return 'Not Found'
    
    for milestone in timeline:
        if milestone.get('milestone') == milestone_name:
            date_str = milestone.get('date', '')
            
            # Handle N/A or empty dates
            if date_str == 'N/A' or not date_str:
                return 'Not Found'
            
            # Extract just the date part (MM/DD/YYYY) if datetime format
            try:
                # Format: "03/24/2025 13:10" -> "03/24/2025"
                if ' ' in date_str:
                    date_part = date_str.split(' ')[0]
                    return date_part
                return date_str
            except:
                return date_str
    
    return 'Not Found'


def find_earliest_appointment(available_times):
    """
    Find the earliest appointment from available times
    
    Args:
        available_times: List of time strings like ["10/10/2025 08:00 AM - 09:00 AM", ...]
        
    Returns:
        Date string (MM/DD/YYYY) of earliest appointment or 'Not Found'
    """
    if not available_times or len(available_times) == 0:
        return 'Not Found'
    
    try:
        # Parse all dates
        parsed_dates = []
        for time_str in available_times:
            try:
                # Format: "10/10/2025 08:00 AM - 09:00 AM"
                # Extract date and start time
                if ' ' in time_str and '-' in time_str:
                    # Split by ' - ' to get start time
                    start_part = time_str.split(' - ')[0]  # "10/10/2025 08:00 AM"
                    
                    # Parse the datetime
                    dt = datetime.strptime(start_part, "%m/%d/%Y %I:%M %p")
                    parsed_dates.append((dt, time_str))
            except Exception as e:
                logger.warning(f"Failed to parse appointment time: {time_str}, error: {e}")
                continue
        
        if not parsed_dates:
            # Fallback: return first item if parsing failed
            first_time = available_times[0]
            if ' ' in first_time:
                return first_time.split(' ')[0]  # Just the date
            return 'Not Found'
        
        # Sort by datetime and get earliest
        parsed_dates.sort(key=lambda x: x[0])
        earliest_dt, earliest_str = parsed_dates[0]
        
        # Return just the date (MM/DD/YYYY)
        return earliest_dt.strftime("%m/%d/%Y")
        
    except Exception as e:
        logger.error(f"Error finding earliest appointment: {e}")
        # Fallback: try to extract date from first item
        if available_times and len(available_times) > 0:
            try:
                first_time = available_times[0]
                if ' ' in first_time:
                    return first_time.split(' ')[0]
            except:
                pass
        return 'Not Found'

