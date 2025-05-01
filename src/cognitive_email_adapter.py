import datetime
import sys
import os
from typing import Dict, List, Any, Optional

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the modules
from ingestionAgent import IngestionAgent, EmailMessage, IngestedThread
from cognitive_email_ecosystem import CognitiveEmailSystem, Email

class CognitiveEmailAdapter:
    """
    Adapter that connects the Ingestion Agent with the Cognitive Email System.
    This allows the hierarchical agent architecture to work with ingested email data.
    """
    def __init__(self, data_path: str = 'data/syntheticEmails.json'):
        self.ingestion_agent = IngestionAgent(data_path)
        self.cognitive_system = CognitiveEmailSystem()
        
    def initialize_system(self):
        """Initialize the cognitive system with basic context."""
        # Set up context data
        self.cognitive_system.context_agent.update_context(
            calendar_events=[
                {
                    'title': 'Project Alpha Review',
                    'start': datetime.datetime.now() + datetime.timedelta(hours=1),
                    'end': datetime.datetime.now() + datetime.timedelta(hours=2),
                    'attendees': ['manager@company.com', 'team1@company.com']
                },
                {
                    'title': 'Weekly Team Sync',
                    'start': datetime.datetime.now() + datetime.timedelta(days=1),
                    'end': datetime.datetime.now() + datetime.timedelta(days=1, hours=1),
                    'attendees': ['team1@company.com', 'team2@company.com', 'design@company.com']
                }
            ],
            location="Office",
            focus_mode="normal"
        )
        
        # Set up organization data
        self.cognitive_system.social_graph.set_org_data(
            hierarchy={
                'manager@company.com': 'executive@company.com',
                'user_email@example.com': 'manager@company.com',
                'team1@company.com': 'user_email@example.com',
                'team2@company.com': 'user_email@example.com',
                'design@company.com': 'user_email@example.com',
                'external@partner.com': 'partner_manager@partner.com',
            },
            teams={
                'Project Alpha': ['user_email@example.com', 'team1@company.com', 'design@company.com'],
                'Project Beta': ['user_email@example.com', 'team2@company.com', 'external@partner.com'],
            }
        )
    
    def convert_to_cognitive_email(self, ingested_thread: IngestedThread) -> List[Email]:
        """Convert an IngestedThread to a list of Email objects for the cognitive system."""
        emails = []
        
        for message in ingested_thread.full_messages:
            # Convert the ingested message to a cognitive Email object
            email = Email(
                sender=message.from_address,
                recipients=message.to_addresses + message.cc_addresses,
                subject=message.subject,
                body=message.body,
                timestamp=message.date,
                thread_id=ingested_thread.thread_id
            )
            emails.append(email)
            
        return emails
    
    def process_threads(self) -> Dict[str, List[Dict[str, Any]]]:
        """Process all ingested threads through the cognitive system."""
        # First, ingest the emails
        ingested_threads = self.ingestion_agent.ingest()
        
        # Initialize the cognitive system
        self.initialize_system()
        
        # Process each thread through the cognitive system
        results = {}
        for ingested_thread in ingested_threads:
            thread_results = []
            
            # Convert and process each message in the thread
            emails = self.convert_to_cognitive_email(ingested_thread)
            for email in emails:
                # Process the email through the cognitive system
                result = self.cognitive_system.process_email(email)
                thread_results.append(result)
            
            # Store results by thread ID
            results[ingested_thread.thread_id] = thread_results
            
        return results
    
    def get_thread_summaries(self) -> List[Dict[str, Any]]:
        """Get a summary of all processed threads."""
        summaries = []
        
        # Process threads if not already done
        if not self.cognitive_system.processed_emails:
            self.process_threads()
        
        # Group emails by thread ID
        thread_map = {}
        for email in self.cognitive_system.processed_emails:
            thread_id = email.thread_id
            if thread_id not in thread_map:
                thread_map[thread_id] = []
            thread_map[thread_id].append(email)
        
        # Create summary for each thread
        for thread_id, emails in thread_map.items():
            # Sort emails by timestamp
            sorted_emails = sorted(emails, key=lambda e: e.timestamp)
            
            # Get the latest email in the thread
            latest_email = sorted_emails[-1]
            
            # Extract unique participants
            participants = set()
            for email in emails:
                participants.add(email.sender)
                participants.update(email.recipients)
            
            # Create the summary
            summary = {
                'thread_id': thread_id,
                'subject': sorted_emails[0].subject,  # Use the subject from the first email
                'latest_snippet': latest_email.body[:100] + "..." if len(latest_email.body) > 100 else latest_email.body,
                'latest_timestamp': latest_email.timestamp.isoformat(),
                'message_count': len(emails),
                'participants': list(participants),
                'prioritization': {
                    'score': latest_email.metadata.get('predicted_priority', 0.5),
                    'intent': latest_email.metadata.get('primary_intent', 'unknown'),
                    'urgency': latest_email.metadata.get('intent_urgency', 'low'),
                },
                'actions_required': any(
                    email.metadata.get('primary_intent') in ['request_action', 'approval', 'seek_input']
                    for email in emails
                ),
                'context_factors': {
                    'related_event': latest_email.metadata.get('related_imminent_event'),
                    'social_importance': latest_email.metadata.get('social_importance'),
                    'org_relationship': latest_email.metadata.get('org_relationship'),
                }
            }
            
            summaries.append(summary)
            
        # Sort summaries by priority score
        summaries.sort(key=lambda s: s['prioritization']['score'], reverse=True)
        
        return summaries
    
    def get_suggested_actions(self) -> List[Dict[str, Any]]:
        """Get suggested actions for all processed emails."""
        actions = []
        
        # Process threads if not already done
        if not self.cognitive_system.processed_emails:
            self.process_threads()
        
        # Find emails with automated handling
        for email in self.cognitive_system.processed_emails:
            # Re-process to get the action plan
            result = self.cognitive_system.process_email(email)
            
            if 'action_plan' in result:
                # Create an action suggestion
                action = {
                    'email_id': id(email),
                    'thread_id': email.thread_id,
                    'subject': email.subject,
                    'sender': email.sender,
                    'timestamp': email.timestamp.isoformat(),
                    'intent': email.metadata.get('primary_intent', 'unknown'),
                    'action_type': result['action_plan']['specialist'],
                    'action_details': result['action_plan'],
                    'priority_score': email.metadata.get('predicted_priority', 0.5)
                }
                
                actions.append(action)
        
        # Sort actions by priority score
        actions.sort(key=lambda a: a['priority_score'], reverse=True)
        
        return actions


# Command-line validation script
if __name__ == "__main__":
    adapter = CognitiveEmailAdapter()
    
    # Process all threads
    print("Processing email threads...")
    adapter.process_threads()
    
    # Get thread summaries
    summaries = adapter.get_thread_summaries()
    print(f"\nFound {len(summaries)} thread summaries")
    
    # Print a few summaries
    for i, summary in enumerate(summaries[:3], 1):
        print(f"\n--- Thread {i}: {summary['subject']} ---")
        print(f"Priority: {summary['prioritization']['score']:.2f}, Intent: {summary['prioritization']['intent']}")
        print(f"Latest: {summary['latest_snippet'][:50]}...")
        print(f"Messages: {summary['message_count']}, Participants: {len(summary['participants'])}")
        print(f"Actions required: {'Yes' if summary['actions_required'] else 'No'}")
    
    # Get suggested actions
    actions = adapter.get_suggested_actions()
    print(f"\nFound {len(actions)} suggested actions")
    
    # Print a few actions
    for i, action in enumerate(actions[:3], 1):
        print(f"\n--- Action {i}: {action['subject']} ---")
        print(f"Action type: {action['action_type']}")
        print(f"From: {action['sender']}")
        print(f"Intent: {action['intent']}")
        print(f"Priority: {action['priority_score']:.2f}") 