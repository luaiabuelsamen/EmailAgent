import datetime
import sys
import os
import json
from typing import Dict, List, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from src.config import ANTHROPIC_API_KEY

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize LangChain with Anthropic
llm = ChatAnthropic(
    model="claude-3-opus-20240229",
    anthropic_api_key=ANTHROPIC_API_KEY,
    temperature=0
)

# Define the output schema
response_schemas = [
    ResponseSchema(name="primary_intent", description="The main purpose or intent of the email"),
    ResponseSchema(name="priority", description="Priority level (high/medium/low) based on content and urgency"),
    ResponseSchema(name="social_context", description="Array of strings describing social and relationship insights"),
    ResponseSchema(name="suggested_actions", description="Array of specific actions to take based on the email"),
    ResponseSchema(name="related_emails", description="Array of objects with subject and from fields (can be empty)")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Create the prompt template
PROMPT_TEMPLATE = """
Analyze this email and provide a detailed analysis:

Email Subject: {subject}
From: {sender}
To: {recipients}
Body: {body}

Please analyze this email and provide:
1. The primary intent of the email
2. Priority level (high/medium/low) based on content and urgency
3. Social context and relationship insights
4. Specific suggested actions

{format_instructions}
"""

prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template(PROMPT_TEMPLATE)
])

# Now import the modules
from src.ingestionAgent import IngestionAgent, EmailMessage, IngestedThread

class Email:
    """Basic email class for cognitive processing."""
    def __init__(self, sender: str, recipients: List[str], subject: str, body: str, 
                 timestamp: datetime.datetime, thread_id: str):
        self.sender = sender
        self.recipients = recipients
        self.subject = subject
        self.body = body
        self.timestamp = timestamp
        self.thread_id = thread_id
        self.metadata = {}

class CognitiveEmailAdapter:
    """
    Adapter that connects the Ingestion Agent with the Cognitive Email System.
    This allows the hierarchical agent architecture to work with ingested email data.
    """
    def __init__(self, data_path: str = 'data/syntheticEmails.json'):
        self.ingestion_agent = IngestionAgent(data_path)
        self.processed_emails = []
        
    def initialize_system(self):
        """Initialize the cognitive system with basic context."""
        pass  # We'll use LangChain for analysis instead
    
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
    
    async def process_email(self, email: Email) -> Dict[str, Any]:
        """Process a single email using LangChain with Claude."""
        try:
            # Format the prompt with email data
            formatted_prompt = prompt.format_messages(
                subject=email.subject,
                sender=email.sender,
                recipients=', '.join(email.recipients),
                body=email.body,
                format_instructions=output_parser.get_format_instructions()
            )
            
            # Get response from Claude through LangChain
            response = llm.invoke(formatted_prompt)
            
            # Parse the structured output
            result = output_parser.parse(response.content)
            
            # Store the email for future reference
            self.processed_emails.append(email)
            
            return result
            
        except Exception as e:
            print(f"Error processing email with LangChain: {e}")
            # Return a basic analysis if processing fails
            return {
                "primary_intent": "unknown",
                "priority": "medium",
                "social_context": [],
                "suggested_actions": ["Review email content"],
                "related_emails": []
            }


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