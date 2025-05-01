import json
import datetime
from typing import Dict, List, Any, Optional

class EmailMessage:
    """Representation of an individual email message."""
    def __init__(self, 
                 id: str,
                 from_address: str, 
                 to_addresses: List[str],
                 date: datetime.datetime,
                 subject: str,
                 snippet: str,
                 body: str,
                 cc_addresses: List[str] = None):
        self.id = id
        self.from_address = from_address
        self.to_addresses = to_addresses
        self.cc_addresses = cc_addresses or []
        self.date = date
        self.subject = subject
        self.snippet = snippet
        self.body = body
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailMessage':
        """Create an EmailMessage from a dictionary representation."""
        date = datetime.datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        return cls(
            id=data['id'],
            from_address=data['from'],
            to_addresses=data['to'],
            cc_addresses=data.get('cc', []),
            date=date,
            subject=data['subject'],
            snippet=data['snippet'],
            body=data['body']
        )


class EmailThread:
    """Representation of an email thread containing multiple messages."""
    def __init__(self, thread_id: str, messages: List[EmailMessage]):
        self.thread_id = thread_id
        self.messages = sorted(messages, key=lambda msg: msg.date)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailThread':
        """Create an EmailThread from a dictionary representation."""
        messages = [EmailMessage.from_dict(msg) for msg in data['messages']]
        return cls(thread_id=data['threadId'], messages=messages)


class IngestedThread:
    """Normalized email thread ready for processing by other agents."""
    def __init__(self, 
                 thread_id: str, 
                 latest_snippet: str, 
                 participants: List[str], 
                 received_at: datetime.datetime,
                 full_messages: List[EmailMessage],
                 subject: str):
        self.thread_id = thread_id
        self.latest_snippet = latest_snippet
        self.participants = participants
        self.received_at = received_at
        self.full_messages = full_messages
        self.subject = subject  # Usually the subject of the first message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the IngestedThread to a dictionary for serialization."""
        return {
            'thread_id': self.thread_id,
            'latest_snippet': self.latest_snippet,
            'participants': self.participants,
            'received_at': self.received_at.isoformat(),
            'subject': self.subject,
            'message_count': len(self.full_messages),
            # We could include full message details here, but they might be large
            # Instead, provide a summary of each message
            'messages_summary': [
                {
                    'id': msg.id,
                    'from': msg.from_address,
                    'date': msg.date.isoformat(),
                    'snippet': msg.snippet
                }
                for msg in self.full_messages
            ]
        }


class IngestionAgent:
    """
    Agent responsible for loading and normalizing email data.
    Acts as the interface between raw email data and the cognitive processing agents.
    """
    def __init__(self, data_path: str = 'data/syntheticEmails.json'):
        self.data_path = data_path
    
    def load_synthetic_emails(self) -> List[Dict[str, Any]]:
        """Load synthetic email data from JSON file."""
        try:
            with open(self.data_path, 'r') as file:
                data = json.load(file)
                return data['threads']
        except FileNotFoundError:
            print(f"Error: Could not find synthetic email data at {self.data_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {self.data_path}")
            return []
    
    def normalize_threads(self, raw_threads: List[Dict[str, Any]]) -> List[IngestedThread]:
        """Convert raw email thread data into normalized IngestedThread objects."""
        normalized_threads = []
        
        for raw_thread in raw_threads:
            # Create EmailThread from raw data
            thread = EmailThread.from_dict(raw_thread)
            
            if not thread.messages:
                continue  # Skip empty threads
            
            # Get the latest message for snippet
            latest_message = thread.messages[-1]
            latest_snippet = latest_message.snippet
            
            # Extract the received time (when the latest message was received)
            received_at = latest_message.date
            
            # Build a unique list of participants
            participants = set()
            for message in thread.messages:
                participants.add(message.from_address)
                participants.update(message.to_addresses)
                participants.update(message.cc_addresses)
            
            # Use the subject of the first message (typically the thread subject)
            subject = thread.messages[0].subject
            
            # Create the normalized thread
            normalized_thread = IngestedThread(
                thread_id=thread.thread_id,
                latest_snippet=latest_snippet,
                participants=list(participants),
                received_at=received_at,
                full_messages=thread.messages,
                subject=subject
            )
            
            normalized_threads.append(normalized_thread)
        
        # Sort threads by received date, most recent first
        normalized_threads.sort(key=lambda t: t.received_at, reverse=True)
        
        return normalized_threads
    
    def ingest(self) -> List[IngestedThread]:
        """Main function to load and normalize email data."""
        raw_threads = self.load_synthetic_emails()
        normalized_threads = self.normalize_threads(raw_threads)
        return normalized_threads


# Command-line validation script
if __name__ == "__main__":
    agent = IngestionAgent()
    threads = agent.ingest()
    
    print(f"Ingested {len(threads)} email threads")
    
    # Print summary of each thread
    for i, thread in enumerate(threads[:5], 1):  # Show first 5 threads
        print(f"\nThread {i}: {thread.subject}")
        print(f"Latest: {thread.latest_snippet[:50]}...")
        print(f"Participants: {', '.join(thread.participants[:3])}{' and more' if len(thread.participants) > 3 else ''}")
        print(f"Received: {thread.received_at}")
        print(f"Messages: {len(thread.full_messages)}") 