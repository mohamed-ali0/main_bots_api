"""
Script to check and monitor query status
"""

import requests
import json
import os
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = 'http://localhost:5000'

# Load user info
USER_TOKEN = None
if os.path.exists('user_info.json'):
    with open('user_info.json', 'r', encoding='utf-8') as f:
        user_info = json.load(f)
        USER_TOKEN = user_info.get('token')
        print(f"[INFO] Loaded token for user: {user_info.get('username')}")
else:
    print("[ERROR] user_info.json not found!")
    print("Please run add_user.py first")
    sys.exit(1)

if not USER_TOKEN:
    print("[ERROR] No token found in user_info.json")
    sys.exit(1)


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def get_all_queries():
    """Get all queries for the user"""
    try:
        response = requests.get(
            f'{BASE_URL}/queries',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Failed to get queries: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None


def get_query_details(query_id):
    """Get detailed information for a specific query"""
    try:
        response = requests.get(
            f'{BASE_URL}/queries/{query_id}',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['query']
        else:
            print(f"[ERROR] Failed to get query {query_id}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None


def format_duration(started_at, completed_at):
    """Calculate and format duration"""
    try:
        start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        if completed_at:
            end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            duration = (end - start).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}m {seconds}s"
        else:
            # Query still running
            now = datetime.utcnow()
            duration = (now - start).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}m {seconds}s (running)"
    except:
        return "N/A"


def print_query_summary(query):
    """Print summary of a single query"""
    print(f"\nQuery ID: {query['query_id']}")
    print(f"Status:   [{query['status'].upper()}]")
    print(f"Platform: {query['platform']}")
    print(f"Started:  {query['started_at']}")
    
    if query['completed_at']:
        print(f"Completed: {query['completed_at']}")
        duration = format_duration(query['started_at'], query['completed_at'])
        print(f"Duration: {duration}")
    else:
        duration = format_duration(query['started_at'], None)
        print(f"Running:  {duration}")
    
    if query.get('summary_stats'):
        stats = query['summary_stats']
        print("\nStatistics:")
        print(f"  Total Containers:     {stats.get('total_containers', 0)}")
        print(f"  Filtered Containers:  {stats.get('filtered_containers', 0)}")
        print(f"  Checked Containers:   {stats.get('checked_containers', 0)}")
        print(f"  Failed Checks:        {stats.get('failed_checks', 0)}")
        print(f"  Total Appointments:   {stats.get('total_appointments', 0)}")
        if 'duration_seconds' in stats:
            mins = stats['duration_seconds'] // 60
            secs = stats['duration_seconds'] % 60
            print(f"  Execution Time:       {mins}m {secs}s")
    
    if query.get('error_message'):
        print(f"\nError: {query['error_message']}")
    
    print("-" * 80)


def list_all_queries():
    """List all queries with their status"""
    print_header("ALL QUERIES")
    
    data = get_all_queries()
    
    if not data:
        return
    
    queries = data.get('queries', [])
    total = data.get('total', 0)
    
    print(f"Total Queries: {total}")
    print(f"Showing: {len(queries)} queries\n")
    
    if not queries:
        print("[INFO] No queries found")
        return
    
    # Group by status
    by_status = {}
    for query in queries:
        status = query['status']
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(query)
    
    # Print summary
    print("Summary by Status:")
    for status, query_list in by_status.items():
        print(f"  {status.upper()}: {len(query_list)}")
    
    print("\n" + "=" * 80)
    
    # Print each query
    for query in queries:
        print_query_summary(query)


def check_specific_query(query_id):
    """Check status of a specific query"""
    print_header(f"QUERY DETAILS: {query_id}")
    
    query = get_query_details(query_id)
    
    if not query:
        return
    
    print_query_summary(query)


def monitor_queries(interval=5, max_iterations=20):
    """Monitor queries with auto-refresh"""
    print_header("QUERY MONITOR - Auto-refresh mode")
    print(f"Refreshing every {interval} seconds")
    print(f"Max iterations: {max_iterations}")
    print("Press Ctrl+C to stop\n")
    
    iteration = 0
    
    try:
        while iteration < max_iterations:
            iteration += 1
            
            # Clear screen (Windows)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"Iteration: {iteration}/{max_iterations}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            data = get_all_queries()
            
            if data:
                queries = data.get('queries', [])
                
                # Count by status
                pending = sum(1 for q in queries if q['status'] == 'pending')
                in_progress = sum(1 for q in queries if q['status'] == 'in_progress')
                completed = sum(1 for q in queries if q['status'] == 'completed')
                failed = sum(1 for q in queries if q['status'] == 'failed')
                
                print(f"\nQuery Status Overview:")
                print(f"  PENDING:     {pending}")
                print(f"  IN_PROGRESS: {in_progress}")
                print(f"  COMPLETED:   {completed}")
                print(f"  FAILED:      {failed}")
                print(f"  TOTAL:       {len(queries)}")
                
                # Show active queries in detail
                active_queries = [q for q in queries if q['status'] in ['pending', 'in_progress']]
                
                if active_queries:
                    print("\n" + "-" * 80)
                    print("ACTIVE QUERIES:")
                    print("-" * 80)
                    
                    for query in active_queries:
                        print(f"\nQuery: {query['query_id']}")
                        print(f"Status: [{query['status'].upper()}]")
                        duration = format_duration(query['started_at'], query.get('completed_at'))
                        print(f"Running: {duration}")
                else:
                    print("\n[INFO] No active queries")
                
                # Check if all done
                if not active_queries and queries:
                    print("\n[SUCCESS] All queries completed!")
                    break
            
            # Wait before next iteration
            if iteration < max_iterations:
                print(f"\nRefreshing in {interval} seconds... (Press Ctrl+C to stop)")
                time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Monitoring stopped by user")


def show_menu():
    """Show interactive menu"""
    print_header("QUERY STATUS CHECKER")
    
    print("Options:")
    print("  1. List all queries")
    print("  2. Check specific query")
    print("  3. Monitor queries (auto-refresh)")
    print("  4. Show only active queries")
    print("  5. Show only completed queries")
    print("  6. Exit")
    print("\n" + "=" * 80)
    
    choice = input("\nEnter option (1-6): ").strip()
    return choice


def show_active_queries():
    """Show only active queries"""
    print_header("ACTIVE QUERIES")
    
    data = get_all_queries()
    
    if not data:
        return
    
    queries = data.get('queries', [])
    active = [q for q in queries if q['status'] in ['pending', 'in_progress']]
    
    if not active:
        print("[INFO] No active queries")
        return
    
    print(f"Found {len(active)} active queries:\n")
    
    for query in active:
        print_query_summary(query)


def show_completed_queries():
    """Show only completed queries"""
    print_header("COMPLETED QUERIES")
    
    try:
        response = requests.get(
            f'{BASE_URL}/queries?status=completed&limit=50',
            headers={'Authorization': f'Bearer {USER_TOKEN}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            queries = data.get('queries', [])
            
            if not queries:
                print("[INFO] No completed queries")
                return
            
            print(f"Found {len(queries)} completed queries:\n")
            
            for query in queries:
                print_query_summary(query)
        else:
            print(f"[ERROR] Failed: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")


def main():
    """Main function"""
    
    # Check if running in interactive mode
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'list':
            list_all_queries()
        elif command == 'monitor':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor_queries(interval=interval)
        elif command == 'active':
            show_active_queries()
        elif command == 'completed':
            show_completed_queries()
        elif command.startswith('q_'):
            # Assume it's a query ID
            check_specific_query(command)
        else:
            print("[ERROR] Unknown command")
            print("\nUsage:")
            print("  python check_query_status.py list          # List all queries")
            print("  python check_query_status.py active        # Show active queries")
            print("  python check_query_status.py completed     # Show completed queries")
            print("  python check_query_status.py monitor [5]   # Monitor with refresh")
            print("  python check_query_status.py q_1_12345     # Check specific query")
    else:
        # Interactive mode
        while True:
            choice = show_menu()
            
            if choice == '1':
                list_all_queries()
                input("\nPress Enter to continue...")
            elif choice == '2':
                query_id = input("Enter Query ID: ").strip()
                check_specific_query(query_id)
                input("\nPress Enter to continue...")
            elif choice == '3':
                interval = input("Refresh interval in seconds [5]: ").strip()
                interval = int(interval) if interval else 5
                monitor_queries(interval=interval)
                input("\nPress Enter to continue...")
            elif choice == '4':
                show_active_queries()
                input("\nPress Enter to continue...")
            elif choice == '5':
                show_completed_queries()
                input("\nPress Enter to continue...")
            elif choice == '6':
                print("\n[INFO] Goodbye!")
                break
            else:
                print("[ERROR] Invalid option")


if __name__ == '__main__':
    main()

