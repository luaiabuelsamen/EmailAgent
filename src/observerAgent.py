import json
import os
import sys
import datetime
from typing import Dict, List, Any, Optional, Set
from collections import Counter

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the IngestedThread model from the ingestion agent
from src.ingestionAgent import IngestedThread

class SessionMemory:
    """In-memory structure to hold bucket definitions and thread assignments."""
    
    def __init__(self):
        self.bucket_definitions: List[str] = []
        self.thread_to_bucket: Dict[str, str] = {}

class ObserverAgent:
    """
    Agent responsible for analyzing email content and user behavior.
    
    The Observer Agent sits on top of the Ingestion Agent and:
    1. Infers meaningful email buckets for categorization
    2. Assigns threads to these buckets
    3. Detects and tracks long-term user traits
    """
    
    def __init__(self, 
                 session_data_path: str = 'data/observerSessionData.json', 
                 long_term_data_path: str = 'data/observerLongTermData.json'):
        self.session_data_path = session_data_path
        self.long_term_data_path = long_term_data_path
        self.session_memory = SessionMemory()
        self.long_term_memory = self._load_long_term_memory()
        
    def _load_session_data(self) -> List[Dict[str, Any]]:
        """Load the synthetic session data for analysis."""
        try:
            with open(self.session_data_path, 'r') as file:
                data = json.load(file)
                return data['threads']
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading session data: {e}")
            return []
    
    def _load_long_term_memory(self) -> Dict[str, Any]:
        """Load the long-term memory store."""
        try:
            with open(self.long_term_data_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading long-term memory: {e}, creating new")
            return {
                "userTraits": {},
                "timestamps": {}
            }
    
    def _save_long_term_memory(self) -> None:
        """Save the long-term memory store."""
        with open(self.long_term_data_path, 'w') as file:
            json.dump(self.long_term_memory, file, indent=2)
    
    def _extract_thread_summary(self, thread: Dict[str, Any]) -> str:
        """Extract a compact summary of a thread for LLM analysis."""
        return f"Subject: {thread['subject']}\nSnippet: {thread['latest_snippet']}"
    
    def _analyze_buckets(self, threads: List[Dict[str, Any]]) -> List[str]:
        """
        Use pattern analysis to suggest bucket categories.
        
        In a real implementation, this would call an LLM with a prompt like:
        "You are an email organizer. Here are X thread headers (subject + snippet).
        Suggest 5-7 human-readable bucket names that cover these threads."
        
        For this prototype, we'll use a rule-based system.
        """
        # Simple bucket suggestion logic based on keyword matching
        bucket_scores = Counter()
        
        # Define patterns for each possible bucket
        patterns = {
            "Work": ["project", "meeting", "review", "budget", "report", "team", "deadline", "client"],
            "Newsletters": ["weekly", "newsletter", "update", "digest", "insights", "trends"],
            "Bills": ["bill", "payment", "due", "reminder", "invoice", "balance", "account"],
            "Social": ["weekend", "dinner", "plans", "party", "invite", "join", "meet up"],
            "Shopping": ["order", "purchase", "shipped", "delivery", "track", "confirmation"],
            "Travel": ["flight", "hotel", "reservation", "booking", "trip", "travel", "itinerary"],
            "Job Search": ["application", "interview", "position", "resume", "job", "career", "recruiting"],
            "Personal Finance": ["account", "bank", "statement", "transaction", "credit", "debit"]
        }
        
        # Search for pattern matches in each thread
        for thread in threads:
            subject_lower = thread['subject'].lower()
            snippet_lower = thread['latest_snippet'].lower()
            combined = subject_lower + " " + snippet_lower
            
            for bucket, keywords in patterns.items():
                for keyword in keywords:
                    if keyword in combined:
                        bucket_scores[bucket] += 1
        
        # Select top buckets (5-7 most common)
        selected_buckets = [bucket for bucket, _ in bucket_scores.most_common(7)]
        
        # Ensure we have at least 5 buckets by adding defaults if necessary
        default_buckets = ["Work", "Personal", "Shopping", "Finance", "Updates"]
        for bucket in default_buckets:
            if bucket not in selected_buckets and len(selected_buckets) < 5:
                selected_buckets.append(bucket)
        
        return selected_buckets
    
    def _assign_thread_to_bucket(self, thread: Dict[str, Any], buckets: List[str]) -> str:
        """
        Assign a thread to the most appropriate bucket.
        
        In a real implementation, this would use an LLM with a prompt like:
        "Buckets: [Bucket1, Bucket2, ...]
        Assign this thread (subject + snippet) to the best bucket.
        Respond with the bucket name only."
        
        For this prototype, we'll use a rule-based system.
        """
        subject_lower = thread['subject'].lower()
        snippet_lower = thread['latest_snippet'].lower()
        combined = subject_lower + " " + snippet_lower
        
        # Define patterns for each possible bucket
        patterns = {
            "Work": ["project", "meeting", "review", "budget", "report", "team", "deadline", "client"],
            "Newsletters": ["weekly", "newsletter", "update", "digest", "insights", "trends"],
            "Bills": ["bill", "payment", "due", "reminder", "invoice", "balance", "account"],
            "Social": ["weekend", "dinner", "plans", "party", "invite", "join", "meet up"],
            "Shopping": ["order", "purchase", "shipped", "delivery", "track", "confirmation"],
            "Travel": ["flight", "hotel", "reservation", "booking", "trip", "travel", "itinerary"],
            "Job Search": ["application", "interview", "position", "resume", "job", "career", "recruiting"],
            "Personal Finance": ["account", "bank", "statement", "transaction", "credit", "debit"],
            "Personal": ["hey", "hello", "hi", "chat", "thanks", "friend", "family"],
            "Updates": ["update", "notification", "alert", "status", "changes"],
            "Finance": ["payment", "financial", "money", "fund", "invoice", "receipt"]
        }
        
        # Score each bucket based on keyword matches
        bucket_scores = {bucket: 0 for bucket in buckets}
        
        # Only score buckets that are in our provided list
        for bucket in buckets:
            if bucket in patterns:
                for keyword in patterns[bucket]:
                    if keyword in combined:
                        bucket_scores[bucket] += 1
        
        # Find the best bucket
        best_bucket = max(bucket_scores.items(), key=lambda x: x[1])
        
        # If no clear winner (score 0 for all), assign to default bucket
        if best_bucket[1] == 0:
            if "Updates" in buckets:
                return "Updates"
            else:
                return buckets[0]  # Just pick the first bucket
        
        return best_bucket[0]
    
    def _analyze_user_traits(self, threads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze threads to identify user traits.
        
        In a real implementation, this would use an LLM with a prompt like:
        "You are a user-insights engine. Here are X thread snippets.
        Identify recurring user activities or life events and set each trait to true/false."
        
        For this prototype, we'll use a rule-based system.
        """
        # Initialize counts for each trait
        trait_counts = {
            "workEmailUser": 0,
            "newsletterSubscriber": 0,
            "frequentShopper": 0,
            "traveler": 0,
            "billPayer": 0,
            "jobSearching": 0,
            "sociallyActive": 0
        }
        
        # Define patterns for each trait
        trait_patterns = {
            "workEmailUser": ["project", "meeting", "review", "budget", "report", "team", "deadline", "client"],
            "newsletterSubscriber": ["weekly", "newsletter", "update", "digest", "insights", "trends"],
            "frequentShopper": ["order", "purchase", "shipped", "delivery", "track", "confirmation"],
            "traveler": ["flight", "hotel", "reservation", "booking", "trip", "travel", "itinerary"],
            "billPayer": ["bill", "payment", "due", "reminder", "invoice", "balance", "account"],
            "jobSearching": ["application", "interview", "position", "resume", "job", "career", "recruiting"],
            "sociallyActive": ["weekend", "dinner", "plans", "party", "invite", "join", "meet up"]
        }
        
        # Count matches for each trait
        for thread in threads:
            subject_lower = thread['subject'].lower()
            snippet_lower = thread['latest_snippet'].lower()
            combined = subject_lower + " " + snippet_lower
            
            for trait, patterns in trait_patterns.items():
                for pattern in patterns:
                    if pattern in combined:
                        trait_counts[trait] += 1
                        break  # Only count once per thread per trait
        
        # Determine which traits are active based on thresholds
        # A trait is active if it appears in 10% or more of threads
        threshold = max(1, len(threads) * 0.1)
        
        traits_result = {}
        current_timestamp = datetime.datetime.now().isoformat()
        timestamps_result = {}
        
        for trait, count in trait_counts.items():
            # Check if the trait is active
            is_active = count >= threshold
            traits_result[trait] = is_active
            
            # Set timestamp for newly detected traits
            existing_state = self.long_term_memory["userTraits"].get(trait, False)
            if is_active and not existing_state:
                timestamps_result[trait] = current_timestamp
            else:
                # Keep the existing timestamp or set to null
                timestamps_result[trait] = self.long_term_memory["timestamps"].get(trait)
        
        return {
            "userTraits": traits_result,
            "timestamps": timestamps_result
        }
    
    def suggest_buckets(self, threads: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Suggest meaningful bucket categories for the current session threads.
        
        Args:
            threads: List of thread dictionaries (optional, will load from file if not provided)
            
        Returns:
            List of 5-7 bucket names appropriate for the threads
        """
        session_threads = threads if threads is not None else self._load_session_data()
        
        # Analyze the threads and suggest appropriate buckets
        suggested_buckets = self._analyze_buckets(session_threads)
        
        # Store the bucket definitions in session memory
        self.session_memory.bucket_definitions = suggested_buckets
        
        return suggested_buckets
    
    def assign_threads_to_buckets(self, 
                                 threads: Optional[List[Dict[str, Any]]] = None, 
                                 buckets: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Assign each thread to the most appropriate bucket.
        
        Args:
            threads: List of thread dictionaries (optional, will load from file if not provided)
            buckets: List of bucket names (optional, will use buckets from session memory if not provided)
            
        Returns:
            Dictionary mapping thread IDs to bucket names
        """
        session_threads = threads if threads is not None else self._load_session_data()
        
        # Use provided buckets or get them from session memory
        if buckets is not None:
            bucket_list = buckets
        elif self.session_memory.bucket_definitions:
            bucket_list = self.session_memory.bucket_definitions
        else:
            # If no buckets are available, suggest them now
            bucket_list = self.suggest_buckets(session_threads)
        
        # Assign each thread to a bucket
        thread_to_bucket = {}
        for thread in session_threads:
            thread_id = thread['thread_id']
            assigned_bucket = self._assign_thread_to_bucket(thread, bucket_list)
            thread_to_bucket[thread_id] = assigned_bucket
        
        # Store the assignments in session memory
        self.session_memory.thread_to_bucket = thread_to_bucket
        
        return thread_to_bucket
    
    def update_user_memory(self, threads: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze threads to identify and update long-term user traits.
        
        Args:
            threads: List of thread dictionaries (optional, will load from file if not provided)
            
        Returns:
            Dictionary with the updated user traits and timestamps
        """
        session_threads = threads if threads is not None else self._load_session_data()
        
        # Analyze the threads to identify user traits
        memory_updates = self._analyze_user_traits(session_threads)
        
        # Update long-term memory with new trait information
        self.long_term_memory["userTraits"].update(memory_updates["userTraits"])
        
        # Update timestamps for traits where appropriate
        for trait, timestamp in memory_updates["timestamps"].items():
            if timestamp is not None:
                self.long_term_memory["timestamps"][trait] = timestamp
        
        # Save the updated long-term memory
        self._save_long_term_memory()
        
        return self.long_term_memory


# Command-line demo
if __name__ == "__main__":
    observer = ObserverAgent()
    
    # 1. Suggest buckets
    print("Suggesting buckets based on session data...")
    buckets = observer.suggest_buckets()
    print(f"Suggested buckets: {buckets}")
    
    # 2. Assign threads to buckets
    print("\nAssigning threads to buckets...")
    assignments = observer.assign_threads_to_buckets()
    print("Thread assignments:")
    for thread_id, bucket in assignments.items():
        print(f"  - {thread_id} -> {bucket}")
    
    # 3. Update user memory
    print("\nUpdating user memory based on thread analysis...")
    memory = observer.update_user_memory()
    print("User traits:")
    for trait, is_active in memory["userTraits"].items():
        timestamp = memory["timestamps"].get(trait, "N/A")
        if is_active:
            status = "ACTIVE"
        else:
            status = "inactive"
        print(f"  - {trait}: {status}")
        if timestamp and is_active:
            print(f"    First detected: {timestamp}") 