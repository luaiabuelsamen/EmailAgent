import sys
import os
import unittest
import json
import tempfile
import shutil
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.observerAgent import ObserverAgent

class ObserverAgentTest(unittest.TestCase):
    def setUp(self):
        """Set up temporary test files."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test session data
        self.session_data_path = os.path.join(self.temp_dir, 'test_session_data.json')
        self.session_data = {
            "threads": [
                {
                    "thread_id": "work1",
                    "subject": "Project Alpha Status Update",
                    "latest_snippet": "Here's the weekly status update for Project Alpha. We're on track for the deadline.",
                    "participants": ["manager@company.com", "user_email@example.com"],
                    "received_at": "2025-04-30T15:00:00Z",
                    "message_count": 1
                },
                {
                    "thread_id": "newsletter1",
                    "subject": "Tech Weekly Newsletter",
                    "latest_snippet": "This week's top tech stories and updates from around the industry.",
                    "participants": ["newsletter@tech.com", "user_email@example.com"],
                    "received_at": "2025-04-30T09:00:00Z",
                    "message_count": 1
                },
                {
                    "thread_id": "bill1",
                    "subject": "Your Electric Bill is Due",
                    "latest_snippet": "Your monthly payment of $75.99 is due in 10 days. Click to pay now.",
                    "participants": ["billing@electric.com", "user_email@example.com"],
                    "received_at": "2025-04-30T10:30:00Z",
                    "message_count": 1
                },
                {
                    "thread_id": "social1",
                    "subject": "Dinner Plans for Friday",
                    "latest_snippet": "Let's meet at 8pm at that new restaurant downtown. Are you available?",
                    "participants": ["friend@personal.com", "user_email@example.com"],
                    "received_at": "2025-04-30T18:15:00Z",
                    "message_count": 2
                },
                {
                    "thread_id": "shopping1",
                    "subject": "Your Order Has Shipped",
                    "latest_snippet": "Your recent purchase has been shipped and will arrive in 2-3 business days.",
                    "participants": ["orders@shop.com", "user_email@example.com"],
                    "received_at": "2025-04-30T11:45:00Z",
                    "message_count": 1
                }
            ]
        }
        with open(self.session_data_path, 'w') as f:
            json.dump(self.session_data, f)
        
        # Create test long-term memory data
        self.long_term_data_path = os.path.join(self.temp_dir, 'test_long_term_data.json')
        self.long_term_data = {
            "userTraits": {
                "workEmailUser": False,
                "newsletterSubscriber": False,
                "frequentShopper": False,
                "traveler": False,
                "billPayer": False,
                "jobSearching": False,
                "sociallyActive": False
            },
            "timestamps": {
                "workEmailUser": None,
                "newsletterSubscriber": None,
                "frequentShopper": None,
                "traveler": None,
                "billPayer": None,
                "jobSearching": None,
                "sociallyActive": None
            }
        }
        with open(self.long_term_data_path, 'w') as f:
            json.dump(self.long_term_data, f)
        
        # Initialize the observer agent with test files
        self.observer = ObserverAgent(
            session_data_path=self.session_data_path,
            long_term_data_path=self.long_term_data_path
        )
    
    def tearDown(self):
        """Clean up temporary test files."""
        shutil.rmtree(self.temp_dir)
    
    def test_bucket_suggestion(self):
        """Test that suggest_buckets returns 5-7 appropriate bucket names."""
        buckets = self.observer.suggest_buckets()
        
        # Check that we have the right number of buckets
        self.assertTrue(5 <= len(buckets) <= 7, f"Expected 5-7 buckets, got {len(buckets)}")
        
        # Check that the returned buckets are strings
        for bucket in buckets:
            self.assertIsInstance(bucket, str)
        
        # Check that buckets cover at least some of our expected categories based on test data
        expected_categories = {"Work", "Newsletters", "Bills", "Social", "Shopping"}
        found_categories = set()
        
        for bucket in buckets:
            for category in expected_categories:
                if category in bucket:
                    found_categories.add(category)
        
        # We should find at least 3 of our expected categories
        self.assertTrue(len(found_categories) >= 3, 
                        f"Expected at least 3 categories from {expected_categories}, found {found_categories}")
    
    def test_thread_assignment(self):
        """Test that threads are assigned to appropriate buckets."""
        # Define some test buckets
        test_buckets = ["Work", "Newsletters", "Bills", "Social", "Shopping"]
        
        # Assign threads to buckets
        assignments = self.observer.assign_threads_to_buckets(buckets=test_buckets)
        
        # Check that all threads are assigned
        self.assertEqual(len(assignments), len(self.session_data["threads"]))
        
        # Check that all thread IDs are in the assignments
        for thread in self.session_data["threads"]:
            thread_id = thread["thread_id"]
            self.assertIn(thread_id, assignments)
        
        # Check specific assignments for known threads
        self.assertEqual(assignments["work1"], "Work")
        self.assertEqual(assignments["newsletter1"], "Newsletters")
        self.assertEqual(assignments["bill1"], "Bills")
        self.assertEqual(assignments["social1"], "Social")
        self.assertEqual(assignments["shopping1"], "Shopping")
    
    def test_user_memory_update(self):
        """Test that user memory is updated correctly based on thread analysis."""
        # Initially all traits should be false
        for trait, value in self.long_term_data["userTraits"].items():
            self.assertFalse(value)
        
        # Update user memory
        updated_memory = self.observer.update_user_memory()
        
        # At least some traits should be detected as true now
        active_traits = [trait for trait, value in updated_memory["userTraits"].items() if value]
        self.assertTrue(len(active_traits) > 0, "No active traits were detected")
        
        # Check that timestamps are updated for active traits
        for trait in active_traits:
            self.assertIsNotNone(updated_memory["timestamps"][trait])
        
        # Verify the specific traits we expect based on our test data
        expected_active_traits = ["workEmailUser", "newsletterSubscriber", "billPayer", 
                                 "sociallyActive", "frequentShopper"]
        
        for trait in expected_active_traits:
            self.assertTrue(updated_memory["userTraits"].get(trait, False), 
                           f"Expected trait '{trait}' to be active but it wasn't")

if __name__ == '__main__':
    unittest.main() 