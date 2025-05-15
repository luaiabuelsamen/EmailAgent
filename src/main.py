from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.cognitive_email_adapter import CognitiveEmailAdapter, Email
from src.ingestionAgent import IngestionAgent, EmailMessage, IngestedThread
from src.observerAgent import ObserverAgent
import asyncio
import dateutil.parser
import json
import hashlib

app = FastAPI(title="Email Analysis API")

# Configure CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://nffoibenjhfmlnohkpjofhlapdcdphni",  # Your extension ID
        "http://localhost:8000",  # Local development
        "http://127.0.0.1:8000"   # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailData(BaseModel):
    subject: Optional[str] = ""
    sender: Optional[str] = ""
    recipients: Optional[List[str]] = []
    body: Optional[str] = None
    snippet: Optional[str] = None
    timestamp: Optional[str] = None
    thread_id: Optional[str] = None
    thread_info: Optional[Dict] = None

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return datetime.now().isoformat()
        return v

    @validator('recipients')
    def validate_recipients(cls, v):
        if v is None:
            return []
        return v

class EmailRequest(BaseModel):
    current_email: Optional[EmailData] = None
    recent_emails: Optional[List[EmailData]] = []

    @validator('recent_emails')
    def validate_recent_emails(cls, v):
        if v is None:
            return []
        return v

class EmailThread(BaseModel):
    thread_id: str
    subject: str
    participants: List[str]
    message_count: int
    last_updated: str
    latest_message: str

class EmailBucket(BaseModel):
    name: str
    count: int
    description: str

class EmailAnalysis(BaseModel):
    primary_intent: Optional[str] = "Unknown intent"
    priority: Optional[str] = "Normal"
    social_context: List[str] = ["General communication"]
    suggested_actions: List[str] = ["Review email content", "Consider response"]
    related_emails: List[dict] = []
    bucket: Optional[str] = "Uncategorized"
    user_traits: Optional[Dict[str, Any]] = {
        "workEmailUser": True,
        "newsletterSubscriber": False,
        "frequentShopper": True,
        "traveler": False,
        "billPayer": True,
        "techSavvy": False,
        "financeFocused": False,
        "healthConscious": False
    }
    thread_summary: Optional[str] = None
    participants_analysis: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = "neutral"
    urgency: Optional[str] = "normal"
    follow_up_needed: Optional[bool] = False
    suggested_response: Optional[str] = "Please review the email content and respond accordingly."
    available_buckets: Optional[List[EmailBucket]] = None
    threads: Optional[List[EmailThread]] = None
    recent_emails_analysis: Optional[List[Dict[str, Any]]] = None

# Initialize the agents
email_adapter = CognitiveEmailAdapter()
ingestion_agent = IngestionAgent()
observer_agent = ObserverAgent()

# Cache for email analysis results
analysis_cache = {}

def get_cache_key(email_data: dict) -> str:
    """Generate a cache key based on email content."""
    # Create a unique key based on email content
    key_data = {
        'subject': email_data.get('subject', ''),
        'from': email_data.get('sender', ''),
        'to': email_data.get('recipients', []),
        'content': email_data.get('body', ''),
        'timestamp': str(email_data.get('timestamp', ''))  # Convert datetime to string
    }
    # Convert to string and hash it
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def parse_date(date_str: str) -> datetime:
    """Parse a date string into a datetime object, handling various formats."""
    try:
        # Try parsing with dateutil first (handles most formats)
        return dateutil.parser.parse(date_str)
    except Exception as e:
        print(f"Error parsing date with dateutil: {e}")
        try:
            # Fallback to datetime.fromisoformat
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            print(f"Error parsing date with fromisoformat: {e}")
            # Last resort: return current time
            return datetime.now()

@app.post("/analyze", response_model=EmailAnalysis)
async def analyze_email(email_request: EmailRequest):
    print("Received analyze request")
    try:
        # Initialize variables
        recent_emails = []
        recent_emails_analysis = []
        all_threads = []
        current_email_analysis = None

        print(f"Processing {len(email_request.recent_emails or [])} recent emails")
        
        # Prepare all emails for batch processing
        if email_request.recent_emails:
            for email in email_request.recent_emails:
                recent_email = Email(
                    sender=email.sender or "",
                    recipients=email.recipients or [],
                    subject=email.subject or "",
                    body=email.body or email.snippet or "",
                    timestamp=parse_date(email.timestamp),
                    thread_id=email.thread_id or ""
                )
                recent_emails.append(recent_email)
                
                thread = IngestedThread(
                    thread_id=email.thread_id or "",
                    latest_snippet=email.snippet or "",
                    participants=[email.sender or ""] + (email.recipients or []),
                    received_at=parse_date(email.timestamp),
                    full_messages=[EmailMessage(
                        id="recent",
                        from_address=email.sender or "",
                        to_addresses=email.recipients or [],
                        date=parse_date(email.timestamp),
                        subject=email.subject or "",
                        snippet=email.snippet or "",
                        body=email.body or email.snippet or ""
                    )],
                    subject=email.subject or ""
                )
                all_threads.append(thread.to_dict())

        # Process current email if available
        if email_request.current_email:
            print(f"Processing current email: {email_request.current_email.subject}")
            current_email = Email(
                sender=email_request.current_email.sender or "",
                recipients=email_request.current_email.recipients or [],
                subject=email_request.current_email.subject or "",
                body=email_request.current_email.body or email_request.current_email.snippet or "",
                timestamp=parse_date(email_request.current_email.timestamp),
                thread_id=email_request.current_email.thread_id or ""
            )
            
            # Generate cache key for the current email
            cache_key = get_cache_key({
                'subject': current_email.subject,
                'sender': current_email.sender,
                'recipients': current_email.recipients,
                'body': current_email.body,
                'timestamp': current_email.timestamp
            })
            
            # Check if we have a cached result
            if cache_key in analysis_cache:
                print(f"Using cached analysis for email: {current_email.subject}")
                return analysis_cache[cache_key]
            
            # Process all emails in a single batch
            print("Analyzing all emails in batch")
            current_email_analysis = await email_adapter.process_email(current_email, recent_emails)

            # Create thread for current email
            current_thread = IngestedThread(
                thread_id=current_email.thread_id,
                latest_snippet=current_email.body[:100],
                participants=[current_email.sender] + current_email.recipients,
                received_at=current_email.timestamp,
                full_messages=[EmailMessage(
                    id="current",
                    from_address=current_email.sender,
                    to_addresses=current_email.recipients,
                    date=current_email.timestamp,
                    subject=current_email.subject,
                    snippet=current_email.body[:100],
                    body=current_email.body
                )],
                subject=current_email.subject
            )
            all_threads.append(current_thread.to_dict())

        print("Getting bucket analysis")
        # Get bucket analysis from observer agent
        buckets = observer_agent.suggest_buckets(all_threads)
        bucket_assignments = observer_agent.assign_threads_to_buckets(all_threads, buckets)
        
        print("Getting user traits")
        # Get user traits analysis
        user_traits = observer_agent.update_user_memory(all_threads)
        
        print("Preparing response")
        # Get available buckets with counts
        available_buckets = [
            EmailBucket(
                name=bucket,
                count=observer_agent.get_bucket_count(bucket),
                description=observer_agent.get_bucket_description(bucket)
            )
            for bucket in buckets
        ]

        # Get related threads if we have a current email
        thread_list = []
        if email_request.current_email:
            related_threads = observer_agent.get_related_threads(all_threads[0])
            thread_list = [
                EmailThread(
                    thread_id=thread['thread_id'],
                    subject=thread['subject'],
                    participants=thread['participants'],
                    message_count=len(thread.get('full_messages', [])),
                    last_updated=thread['received_at'],
                    latest_message=thread['latest_snippet']
                )
                for thread in related_threads
            ]

        print("Sending response")
        # Combine all analyses
        response = EmailAnalysis(
            primary_intent=current_email_analysis.get("primary_intent") if current_email_analysis else "Unknown intent",
            priority=current_email_analysis.get("priority") if current_email_analysis else "Normal",
            social_context=current_email_analysis.get("social_context", []) if current_email_analysis else ["General communication"],
            suggested_actions=current_email_analysis.get("suggested_actions", []) if current_email_analysis else ["Review email content", "Consider response"],
            related_emails=current_email_analysis.get("related_emails", []) if current_email_analysis else [],
            bucket=bucket_assignments.get(all_threads[0]['thread_id']) if all_threads else "Uncategorized",
            user_traits=user_traits.get("userTraits", {
                "workEmailUser": True,
                "newsletterSubscriber": False,
                "frequentShopper": True,
                "traveler": False,
                "billPayer": True,
                "techSavvy": False,
                "financeFocused": False,
                "healthConscious": False
            }),
            thread_summary=all_threads[0]['latest_snippet'] if all_threads else None,
            participants_analysis={
                "sender": email_request.current_email.sender if email_request.current_email else None,
                "recipients": email_request.current_email.recipients if email_request.current_email else [],
                "total_participants": len(email_request.current_email.recipients) + 1 if email_request.current_email else 0
            } if email_request.current_email else None,
            sentiment=current_email_analysis.get("sentiment", "neutral") if current_email_analysis else "neutral",
            urgency=current_email_analysis.get("urgency", "normal") if current_email_analysis else "normal",
            follow_up_needed=current_email_analysis.get("follow_up_needed", False) if current_email_analysis else False,
            suggested_response=current_email_analysis.get("suggested_response") if current_email_analysis else "Please review the email content and respond accordingly.",
            available_buckets=available_buckets,
            threads=thread_list,
            recent_emails_analysis=recent_emails_analysis
        )
        
        # Cache the result
        analysis_cache[cache_key] = response
        
        return response
        
    except Exception as e:
        print(f"Error in analyze_email: {e}")
        # Return default analysis if there's an error
        return EmailAnalysis(
            primary_intent="Unknown intent",
            priority="Normal",
            social_context=["General communication"],
            suggested_actions=["Review email content", "Consider response"],
            related_emails=[],
            bucket="Uncategorized",
            user_traits={
                "workEmailUser": True,
                "newsletterSubscriber": False,
                "frequentShopper": True,
                "traveler": False,
                "billPayer": True,
                "techSavvy": False,
                "financeFocused": False,
                "healthConscious": False
            },
            sentiment="neutral",
            urgency="normal",
            follow_up_needed=False,
            suggested_response="Please review the email content and respond accordingly.",
            recent_emails_analysis=[]
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 