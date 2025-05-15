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
    4. Analyzes sentiment and urgency
    5. Provides thread summaries and related context
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
        """
        # Define patterns for each possible bucket with more detailed keywords
        patterns = {
            "Work": ["project", "meeting", "review", "budget", "report", "team", "deadline", "client", "presentation", "agenda", "minutes", "action items"],
            "Newsletters": ["weekly", "newsletter", "update", "digest", "insights", "trends", "subscribe", "unsubscribe", "marketing", "promotion"],
            "Bills": ["bill", "payment", "due", "reminder", "invoice", "balance", "account", "statement", "transaction", "receipt", "subscription"],
            "Social": ["weekend", "dinner", "plans", "party", "invite", "join", "meet up", "catch up", "coffee", "lunch", "dinner"],
            "Shopping": ["order", "purchase", "shipped", "delivery", "track", "confirmation", "cart", "checkout", "discount", "sale", "receipt"],
            "Travel": ["flight", "hotel", "reservation", "booking", "trip", "travel", "itinerary", "airport", "check-in", "boarding pass"],
            "Job Search": ["application", "interview", "position", "resume", "job", "career", "recruiting", "hiring", "opportunity", "role"],
            "Personal Finance": ["account", "bank", "statement", "transaction", "credit", "debit", "investment", "portfolio", "retirement", "savings"],
            "Updates": ["update", "notification", "alert", "reminder", "system", "maintenance", "status", "change", "new feature"],
            "Personal": ["family", "friend", "personal", "private", "catch up", "how are you", "hope you're well", "thinking of you"]
        }
        
        # Initialize bucket scores
        bucket_scores = Counter()
        
        # Score each thread against patterns
        for thread in threads:
            combined = f"{thread['subject']} {thread['latest_snippet']}".lower()
            for bucket, keywords in patterns.items():
                for keyword in keywords:
                    if keyword in combined:
                        bucket_scores[bucket] += 1
        
        # Return top 5 buckets by score
        return [bucket for bucket, _ in bucket_scores.most_common(5)]
    
    def _analyze_user_traits(self, threads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze threads to identify user traits with more detailed analysis.
        """
        # Initialize trait analysis
        trait_analysis = {
            "userTraits": {
                "workEmailUser": False,
                "newsletterSubscriber": False,
                "frequentShopper": False,
                "traveler": False,
                "billPayer": False,
                "jobSearching": False,
                "sociallyActive": False,
                "techSavvy": False,
                "financeFocused": False,
                "healthConscious": False
            },
            "timestamps": {}
        }
        
        # Analyze each thread for traits
        for thread in threads:
            combined = f"{thread['subject']} {thread['latest_snippet']}".lower()
            
            # Work email analysis
            if any(word in combined for word in ["meeting", "project", "deadline", "client", "team"]):
                trait_analysis["userTraits"]["workEmailUser"] = True
            
            # Newsletter analysis
            if any(word in combined for word in ["newsletter", "subscribe", "digest", "update"]):
                trait_analysis["userTraits"]["newsletterSubscriber"] = True
            
            # Shopping analysis
            if any(word in combined for word in ["order", "purchase", "shipped", "delivery"]):
                trait_analysis["userTraits"]["frequentShopper"] = True
            
            # Travel analysis
            if any(word in combined for word in ["flight", "hotel", "booking", "travel"]):
                trait_analysis["userTraits"]["traveler"] = True
            
            # Bill analysis
            if any(word in combined for word in ["bill", "payment", "invoice", "statement"]):
                trait_analysis["userTraits"]["billPayer"] = True
            
            # Job search analysis
            if any(word in combined for word in ["job", "career", "interview", "application"]):
                trait_analysis["userTraits"]["jobSearching"] = True
            
            # Social activity analysis
            if any(word in combined for word in ["meet", "catch up", "coffee", "lunch"]):
                trait_analysis["userTraits"]["sociallyActive"] = True
            
            # Tech savviness analysis
            if any(word in combined for word in ["app", "software", "update", "tech"]):
                trait_analysis["userTraits"]["techSavvy"] = True
            
            # Finance focus analysis
            if any(word in combined for word in ["investment", "portfolio", "retirement", "savings"]):
                trait_analysis["userTraits"]["financeFocused"] = True
            
            # Health consciousness analysis
            if any(word in combined for word in ["fitness", "wellness", "health", "nutrition"]):
                trait_analysis["userTraits"]["healthConscious"] = True
            
            # Update timestamps for active traits
            for trait, is_active in trait_analysis["userTraits"].items():
                if is_active:
                    trait_analysis["timestamps"][trait] = thread['received_at']
        
        return trait_analysis
    
    def _analyze_sentiment_and_urgency(self, thread: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze thread content for sentiment and urgency.
        """
        combined = f"{thread['subject']} {thread['latest_snippet']}".lower()
        
        # Sentiment analysis
        positive_words = ["thank", "great", "appreciate", "excellent", "wonderful", "happy", "pleased"]
        negative_words = ["sorry", "apologize", "issue", "problem", "concern", "unfortunately", "regret"]
        
        sentiment = "neutral"
        if any(word in combined for word in positive_words):
            sentiment = "positive"
        elif any(word in combined for word in negative_words):
            sentiment = "negative"
        
        # Urgency analysis
        urgency_words = ["urgent", "asap", "important", "immediate", "critical", "emergency", "deadline"]
        urgency = "normal"
        if any(word in combined for word in urgency_words):
            urgency = "high"
        
        return {
            "sentiment": sentiment,
            "urgency": urgency
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

    def get_bucket_count(self, bucket: str) -> int:
        """Get the number of emails in a bucket."""
        count = 0
        for thread_id, assigned_bucket in self.session_memory.thread_to_bucket.items():
            if assigned_bucket == bucket:
                count += 1
        return count

    def get_bucket_description(self, bucket: str) -> str:
        """Get a detailed description for a bucket."""
        descriptions = {
            "Work": "Professional communications, project updates, meetings, and work-related tasks",
            "Newsletters": "Subscribed newsletters, marketing communications, and promotional updates",
            "Bills": "Financial statements, payment reminders, invoices, and subscription notices",
            "Social": "Personal communications, social events, and informal catch-ups",
            "Shopping": "Online orders, delivery notifications, and purchase confirmations",
            "Travel": "Flight bookings, hotel reservations, and travel itineraries",
            "Job Search": "Job applications, interview communications, and career opportunities",
            "Personal Finance": "Banking statements, investment updates, and financial planning",
            "Personal": "Private communications with family and friends",
            "Updates": "System notifications, service updates, and automated alerts",
            "Finance": "Financial transactions, account statements, and money management"
        }
        return descriptions.get(bucket, f"Emails categorized as {bucket}")

    def get_related_threads(self, thread: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get threads related to the given thread."""
        related_threads = []
        current_bucket = self.session_memory.thread_to_bucket.get(thread['thread_id'])
        
        if not current_bucket:
            return []

        # Get all threads in the same bucket
        for thread_id, bucket in self.session_memory.thread_to_bucket.items():
            if bucket == current_bucket and thread_id != thread['thread_id']:
                # Load thread data
                thread_data = self._load_thread_data(thread_id)
                if thread_data:
                    related_threads.append(thread_data)

        # Sort by date (most recent first) and limit to 5 threads
        related_threads.sort(key=lambda x: x['received_at'], reverse=True)
        return related_threads[:5]

    def _load_thread_data(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Load thread data from session data."""
        threads = self._load_session_data()
        for thread in threads:
            if thread['thread_id'] == thread_id:
                return thread
        return None

    def _assign_thread_to_bucket(self, thread: Dict[str, Any], buckets: List[str]) -> str:
        """
        Assign a single thread to the most appropriate bucket.
        
        Args:
            thread: Thread dictionary containing subject and snippet
            buckets: List of available bucket names
            
        Returns:
            The name of the most appropriate bucket
        """
        # Define patterns for each bucket with more detailed keywords
        patterns = {
            "Work": ["project", "meeting", "review", "budget", "report", "team", "deadline", "client", "presentation", "agenda", "minutes", "action items"],
            "Newsletters": ["weekly", "newsletter", "update", "digest", "insights", "trends", "subscribe", "unsubscribe", "marketing", "promotion"],
            "Bills": ["bill", "payment", "due", "reminder", "invoice", "balance", "account", "statement", "transaction", "receipt", "subscription"],
            "Social": ["weekend", "dinner", "plans", "party", "invite", "join", "meet up", "catch up", "coffee", "lunch", "dinner"],
            "Shopping": ["order", "purchase", "shipped", "delivery", "track", "confirmation", "cart", "checkout", "discount", "sale", "receipt"],
            "Travel": ["flight", "hotel", "reservation", "booking", "trip", "travel", "itinerary", "airport", "check-in", "boarding pass"],
            "Job Search": ["application", "interview", "position", "resume", "job", "career", "recruiting", "hiring", "opportunity", "role"],
            "Personal Finance": ["account", "bank", "statement", "transaction", "credit", "debit", "investment", "portfolio", "retirement", "savings"],
            "Updates": ["update", "notification", "alert", "reminder", "system", "maintenance", "status", "change", "new feature"],
            "Personal": ["family", "friend", "personal", "private", "catch up", "how are you", "hope you're well", "thinking of you"]
        }
        
        # Initialize bucket scores
        bucket_scores = {bucket: 0 for bucket in buckets}
        
        # Combine subject and snippet for analysis
        combined = f"{thread['subject']} {thread.get('latest_snippet', '')}".lower()
        
        # Score each bucket based on keyword matches
        for bucket in buckets:
            if bucket in patterns:
                for keyword in patterns[bucket]:
                    if keyword in combined:
                        bucket_scores[bucket] += 1
        
        # Find the bucket with the highest score
        if not bucket_scores:
            return "Uncategorized"
            
        max_score = max(bucket_scores.values())
        if max_score == 0:
            return "Uncategorized"
            
        # Return the bucket with the highest score
        for bucket, score in bucket_scores.items():
            if score == max_score:
                return bucket
                
        return "Uncategorized"

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