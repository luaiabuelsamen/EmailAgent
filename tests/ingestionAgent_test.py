import sys
import os
import unittest
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestionAgent import IngestionAgent, IngestedThread, EmailMessage

class IngestionAgentTest(unittest.TestCase):
    def setUp(self):
        self.agent = IngestionAgent()
    
    def test_ingest_returns_array(self):
        """Test that ingest() returns a non-empty array of IngestedThread objects."""
        threads = self.agent.ingest()
        self.assertIsInstance(threads, list)
        self.assertTrue(len(threads) > 0)
        self.assertIsInstance(threads[0], IngestedThread)
    
    def test_thread_has_expected_properties(self):
        """Test that each thread has the expected properties."""
        threads = self.agent.ingest()
        thread = threads[0]  # Get the first thread
        
        # Check that all required properties exist
        self.assertTrue(hasattr(thread, 'thread_id'))
        self.assertTrue(hasattr(thread, 'latest_snippet'))
        self.assertTrue(hasattr(thread, 'participants'))
        self.assertTrue(hasattr(thread, 'received_at'))
        self.assertTrue(hasattr(thread, 'full_messages'))
        self.assertTrue(hasattr(thread, 'subject'))
        
        # Check types
        self.assertIsInstance(thread.thread_id, str)
        self.assertIsInstance(thread.latest_snippet, str)
        self.assertIsInstance(thread.participants, list)
        self.assertIsInstance(thread.received_at, datetime)
        self.assertIsInstance(thread.full_messages, list)
        self.assertIsInstance(thread.subject, str)
        
        # Check that participants list is not empty
        self.assertTrue(len(thread.participants) > 0)
        
        # Check that full_messages contains EmailMessage objects
        self.assertTrue(len(thread.full_messages) > 0)
        self.assertIsInstance(thread.full_messages[0], EmailMessage)
    
    def test_threads_are_sorted_by_date(self):
        """Test that threads are sorted by received_at date (newest first)."""
        threads = self.agent.ingest()
        
        # Check at least the first two threads (if available) to verify sort order
        if len(threads) >= 2:
            self.assertGreaterEqual(threads[0].received_at, threads[1].received_at)
    
    def test_participants_list_contains_all_addresses(self):
        """Test that participants list contains all email addresses from the thread."""
        threads = self.agent.ingest()
        
        # Find a thread with multiple messages
        multi_message_thread = None
        for thread in threads:
            if len(thread.full_messages) > 1:
                multi_message_thread = thread
                break
        
        if multi_message_thread:
            # Collect all unique addresses from messages manually
            expected_participants = set()
            for msg in multi_message_thread.full_messages:
                expected_participants.add(msg.from_address)
                expected_participants.update(msg.to_addresses)
                expected_participants.update(msg.cc_addresses)
            
            # Convert sets to sorted lists for comparison
            expected = sorted(list(expected_participants))
            actual = sorted(multi_message_thread.participants)
            
            # Verify that all participants are captured
            self.assertEqual(expected, actual)
    
    def test_latest_snippet_from_most_recent_message(self):
        """Test that latest_snippet comes from the most recent message."""
        threads = self.agent.ingest()
        
        # Find a thread with multiple messages
        multi_message_thread = None
        for thread in threads:
            if len(thread.full_messages) > 1:
                multi_message_thread = thread
                break
        
        if multi_message_thread:
            # Get the most recent message
            messages = sorted(multi_message_thread.full_messages, key=lambda m: m.date)
            most_recent_message = messages[-1]
            
            # Verify that the thread's latest_snippet matches
            self.assertEqual(multi_message_thread.latest_snippet, most_recent_message.snippet)

if __name__ == '__main__':
    unittest.main() 