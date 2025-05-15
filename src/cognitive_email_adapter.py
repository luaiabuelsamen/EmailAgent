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
    ResponseSchema(name="related_emails", description="Array of objects with subject and from fields (can be empty)"),
    ResponseSchema(name="sentiment", description="Overall sentiment of the email (positive/neutral/negative)"),
    ResponseSchema(name="urgency", description="Urgency level (high/normal/low)"),
    ResponseSchema(name="follow_up_needed", description="Whether follow-up is required (true/false)"),
    ResponseSchema(name="suggested_response", description="Suggested response template or key points"),
    ResponseSchema(name="bucket", description="Suggested email category/bucket"),
    ResponseSchema(name="user_traits", description="Dictionary of user traits inferred from the email"),
    ResponseSchema(name="thread_summary", description="Summary of the email thread if available"),
    ResponseSchema(name="participants_analysis", description="Analysis of email participants and their roles")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Create the prompt template
PROMPT_TEMPLATE = """
You are an expert email analyst. Your task is to analyze the following emails and provide a comprehensive analysis for each one.

{body}

Please analyze each email considering the following aspects:

1. Primary Intent:
   - What is the main purpose of this email?
   - Is it informational, requesting action, or something else?
   - Consider both explicit and implicit intentions
   - How does it relate to other emails in the batch?

2. Priority Assessment:
   - Evaluate urgency based on content, tone, and context
   - Consider time-sensitive elements and deadlines
   - Look for explicit or implicit deadlines
   - Compare with priority patterns in other emails
   - Rate as high/medium/low with confidence score

3. Social Context:
   - Analyze the relationship between sender and recipients
   - Identify any power dynamics or professional relationships
   - Note any cultural or contextual cues
   - Consider the tone and formality level
   - Compare with communication patterns in other emails
   - List specific social insights as separate points

4. Suggested Actions:
   - List specific, actionable steps
   - Prioritize actions based on importance
   - Consider both immediate and follow-up actions
   - Include any necessary preparation or research
   - Reference similar actions from other emails if relevant

5. Related Context:
   - Identify any related topics or threads
   - Note any dependencies or prerequisites
   - Consider historical context from other emails
   - List specific related emails with their relevance

6. Sentiment Analysis:
   - Evaluate the overall tone and emotional content
   - Identify any emotional triggers or concerns
   - Consider both explicit and implicit sentiment
   - Compare with sentiment patterns in other emails
   - Provide confidence score for sentiment assessment

7. Urgency Assessment:
   - Determine if immediate action is required
   - Identify any time-sensitive elements
   - Consider both explicit and implicit urgency
   - Compare with urgency patterns in other emails
   - Provide confidence score for urgency assessment

8. Follow-up Requirements:
   - Determine if follow-up is needed
   - Identify what type of follow-up is appropriate
   - Consider both immediate and long-term follow-up needs
   - Reference similar follow-up patterns from other emails

9. Suggested Response:
   - Provide a template or key points for response
   - Consider tone and formality
   - Include necessary context and references
   - Reference successful response patterns from other emails

10. Categorization:
    - Suggest appropriate email category/bucket
    - Consider both content and context
    - Identify any relevant tags or labels
    - Compare with categorization patterns in other emails

11. User Traits:
    - Identify any user traits or preferences
    - Consider communication patterns
    - Note any recurring themes or interests
    - Compare with patterns from other emails

12. Thread Analysis:
    - Summarize the thread if available
    - Identify key participants and their roles
    - Note any important context or history
    - Compare with patterns from other threads

For each email, provide your analysis in a structured format that includes all the requested fields. For each field, provide detailed reasoning and confidence scores where applicable.

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
    
    async def process_email(self, email: Email, recent_emails: List[Email] = None) -> Dict[str, Any]:
        """Process a single email using LangChain with Claude."""
        try:
            print(f"Starting to process email: {email.subject}")
            
            # If this is the first email in a batch, process all emails together
            if recent_emails and not self.processed_emails:
                print(f"Processing batch of {len(recent_emails) + 1} emails")
                all_emails = [email] + recent_emails
                
                # Format all emails for analysis
                emails_context = "Emails to Analyze:\n"
                for i, current_email in enumerate(all_emails, 1):
                    emails_context += f"\nEmail {i}:\n"
                    emails_context += f"Subject: {current_email.subject}\n"
                    emails_context += f"From: {current_email.sender}\n"
                    emails_context += f"Date: {current_email.timestamp}\n"
                    emails_context += f"Body: {current_email.body}\n"
                    emails_context += f"Thread ID: {current_email.thread_id}\n"
                    emails_context += "---\n"

                print("Formatting prompt for batch analysis")
                # Format the prompt with all emails
                formatted_prompt = prompt.format_messages(
                    subject="Multiple Emails Analysis",
                    sender="Multiple Senders",
                    recipients="Multiple Recipients",
                    body=emails_context,
                    recent_emails="",  # No need for recent emails context since we're analyzing all at once
                    format_instructions=output_parser.get_format_instructions()
                )
                
                print("Sending batch request to Claude")
                # Get response from Claude through LangChain
                response = llm.invoke(formatted_prompt)
                print("Received response from Claude")
                
                print("Parsing structured output")
                # Parse the structured output
                result = output_parser.parse(response.content)
                
                # Store all emails as processed
                self.processed_emails.extend(all_emails)
                
                # Extract the analysis for the current email
                current_email_analysis = self._extract_email_analysis(result, email)
                return current_email_analysis
            
            # If this email was already processed in a batch, return its analysis
            if email in self.processed_emails:
                print(f"Email {email.subject} was already processed in batch")
                return self._get_cached_analysis(email)
            
            # If this is a single email analysis
            print("Processing single email")
            formatted_prompt = prompt.format_messages(
                subject=email.subject,
                sender=email.sender,
                recipients=', '.join(email.recipients),
                body=email.body,
                recent_emails="",  # No recent emails context for single analysis
                format_instructions=output_parser.get_format_instructions()
            )
            
            print("Sending request to Claude")
            response = llm.invoke(formatted_prompt)
            print("Received response from Claude")
            
            print("Parsing structured output")
            result = output_parser.parse(response.content)
            
            # Store the email for future reference
            self.processed_emails.append(email)
            
            return self._format_result(result)
            
        except Exception as e:
            print(f"Error processing email with LangChain: {e}")
            return self._get_default_analysis()

    def _extract_email_analysis(self, batch_result: Dict[str, Any], email: Email) -> Dict[str, Any]:
        """Extract the analysis for a specific email from the batch result."""
        # For now, return the batch result as is
        # In the future, we can parse the batch result to extract specific email analysis
        return self._format_result(batch_result)

    def _get_cached_analysis(self, email: Email) -> Dict[str, Any]:
        """Get cached analysis for an email that was processed in a batch."""
        # For now, return a default analysis
        # In the future, we can store and retrieve specific analyses for each email
        return self._get_default_analysis()

    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the analysis result."""
        # Ensure social_context is a list
        if isinstance(result.get('social_context'), str):
            result['social_context'] = [result['social_context']]
        elif not isinstance(result.get('social_context'), list):
            result['social_context'] = ["General communication"]
        
        # Ensure suggested_actions is a list
        if isinstance(result.get('suggested_actions'), str):
            result['suggested_actions'] = [result['suggested_actions']]
        elif not isinstance(result.get('suggested_actions'), list):
            result['suggested_actions'] = ["Review email content"]
        
        return result

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis values."""
        return {
            "primary_intent": "unknown",
            "priority": "medium",
            "social_context": ["General communication"],
            "suggested_actions": ["Review email content"],
            "related_emails": [],
            "sentiment": "neutral",
            "urgency": "normal",
            "follow_up_needed": False,
            "suggested_response": "Please review the email content and respond accordingly.",
            "bucket": "Uncategorized",
            "user_traits": {},
            "thread_summary": None,
            "participants_analysis": None
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