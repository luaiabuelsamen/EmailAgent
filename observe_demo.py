#!/usr/bin/env python3
"""
Demo script for the Observer Agent in the Cognitive Email Ecosystem.

This script demonstrates the core capabilities of the Observer Agent:
1. Suggesting buckets based on email content
2. Assigning threads to appropriate buckets
3. Updating long-term user memory based on email patterns
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the Observer Agent
from src.observerAgent import ObserverAgent

def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def print_buckets(buckets: List[str]) -> None:
    """Print the bucket list in a formatted way."""
    print("\nSuggested Email Buckets:")
    print("-" * 30)
    for i, bucket in enumerate(buckets, 1):
        print(f"{i}. {bucket}")

def print_thread_assignments(assignments: Dict[str, str], threads: List[Dict[str, Any]]) -> None:
    """Print thread assignments grouped by bucket."""
    # Create a lookup for thread details
    thread_lookup = {thread['thread_id']: thread for thread in threads}
    
    # Group threads by bucket
    buckets_to_threads = {}
    for thread_id, bucket in assignments.items():
        if bucket not in buckets_to_threads:
            buckets_to_threads[bucket] = []
        buckets_to_threads[bucket].append(thread_id)
    
    # Print the groupings
    print("\nThread Assignments:")
    print("-" * 30)
    
    for bucket, thread_ids in sorted(buckets_to_threads.items()):
        print(f"\n📁 {bucket} ({len(thread_ids)} threads)")
        print("-" * 30)
        
        for thread_id in thread_ids:
            thread = thread_lookup.get(thread_id, {})
            subject = thread.get('subject', 'Unknown Subject')
            sender = thread.get('participants', ['unknown@example.com'])[0]
            print(f"  - {subject} (from: {sender})")

def print_user_traits(memory: Dict[str, Any]) -> None:
    """Print user traits in a formatted way."""
    traits = memory.get('userTraits', {})
    timestamps = memory.get('timestamps', {})
    
    print("\nDetected User Traits:")
    print("-" * 30)
    
    active_traits = [trait for trait, is_active in traits.items() if is_active]
    inactive_traits = [trait for trait, is_active in traits.items() if not is_active]
    
    if active_traits:
        print("\n✅ Active Traits:")
        for trait in active_traits:
            timestamp = timestamps.get(trait)
            timestamp_str = f"(first seen: {timestamp})" if timestamp else ""
            print(f"  - {trait.replace('_', ' ').title()} {timestamp_str}")
    
    if inactive_traits:
        print("\n❌ Inactive Traits:")
        for trait in inactive_traits:
            print(f"  - {trait.replace('_', ' ').title()}")

def create_timeline_view(threads: List[Dict[str, Any]], assignments: Dict[str, str]) -> None:
    """Create a timeline view of the threads with their bucket assignments."""
    # Sort threads by received_at
    sorted_threads = sorted(threads, key=lambda t: t['received_at'], reverse=True)
    
    print("\nEmail Timeline with Bucket Assignments:")
    print("-" * 50)
    
    current_date = None
    for thread in sorted_threads:
        # Parse the date
        received_at = datetime.fromisoformat(thread['received_at'].replace('Z', '+00:00'))
        thread_date = received_at.strftime('%Y-%m-%d')
        
        # Print date header if it changed
        if thread_date != current_date:
            current_date = thread_date
            print(f"\n📅 {current_date}")
        
        # Get the bucket assignment
        bucket = assignments.get(thread['thread_id'], 'Unassigned')
        
        # Print the thread info
        time_str = received_at.strftime('%H:%M')
        print(f"  {time_str} - [{bucket}] {thread['subject']}")

def main() -> None:
    """Main function to demonstrate the Observer Agent."""
    print_section_header("Observer Agent Demonstration")
    
    # Initialize the Observer Agent
    observer = ObserverAgent()
    
    # Load session data for display
    try:
        with open('data/observerSessionData.json', 'r') as f:
            session_data = json.load(f)
            threads = session_data.get('threads', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading session data: {e}")
        return
    
    # Step 1: Suggest buckets
    print_section_header("1. Bucket Suggestion")
    print("Analyzing email content to suggest meaningful bucket categories...")
    buckets = observer.suggest_buckets()
    print_buckets(buckets)
    
    # Step 2: Assign threads to buckets
    print_section_header("2. Thread Assignment")
    print("Assigning each thread to the most appropriate bucket...")
    assignments = observer.assign_threads_to_buckets()
    print_thread_assignments(assignments, threads)
    
    # Step 3: Update user memory
    print_section_header("3. User Memory Update")
    print("Analyzing thread patterns to identify user traits...")
    memory = observer.update_user_memory()
    print_user_traits(memory)
    
    # Bonus: Timeline View
    print_section_header("Bonus: Timeline View")
    create_timeline_view(threads, assignments)
    
    print("\n")
    print_section_header("Demo Complete")
    print("\nThe Observer Agent has successfully:")
    print("1. Suggested email buckets based on content analysis")
    print("2. Assigned threads to appropriate buckets")
    print("3. Updated long-term user memory with detected traits")
    print("\nThis demonstrates how the hierarchical agent architecture can")
    print("provide increasingly sophisticated email processing:")
    print("• Ingestion Agent → Observer Agent → Cognitive System")

if __name__ == "__main__":
    main() 