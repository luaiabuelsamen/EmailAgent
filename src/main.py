from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.cognitive_email_adapter import CognitiveEmailAdapter, Email
from src.ingestionAgent import IngestionAgent, EmailMessage, IngestedThread
from src.observerAgent import ObserverAgent

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
    subject: str
    sender: str
    recipients: List[str]
    body: Optional[str]
    snippet: Optional[str]
    timestamp: str
    thread_id: Optional[str]
    thread_info: Optional[Dict] = None

class EmailRequest(BaseModel):
    current_email: Optional[EmailData]
    recent_emails: List[EmailData]

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
    primary_intent: Optional[str]
    priority: Optional[str]
    social_context: List[str]
    suggested_actions: List[str]
    related_emails: List[dict]
    bucket: Optional[str] = None
    user_traits: Optional[Dict[str, Any]] = None
    thread_summary: Optional[str] = None
    participants_analysis: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    follow_up_needed: Optional[bool] = None
    suggested_response: Optional[str] = None
    available_buckets: Optional[List[EmailBucket]] = None
    threads: Optional[List[EmailThread]] = None
    recent_emails_analysis: Optional[List[Dict[str, Any]]] = None

# Initialize the agents
email_adapter = CognitiveEmailAdapter()
ingestion_agent = IngestionAgent()
observer_agent = ObserverAgent()

@app.post("/analyze", response_model=EmailAnalysis)
async def analyze_email(email_request: EmailRequest):
    try:
        all_threads = []
        current_email_analysis = None

        # Process current email if available
        if email_request.current_email:
            current_email = Email(
                sender=email_request.current_email.sender,
                recipients=email_request.current_email.recipients,
                subject=email_request.current_email.subject,
                body=email_request.current_email.body or email_request.current_email.snippet or "",
                timestamp=datetime.fromisoformat(email_request.current_email.timestamp.replace('Z', '+00:00')),
                thread_id=email_request.current_email.thread_id or ""
            )
            
            # Process the current email through the cognitive adapter
            current_email_analysis = await email_adapter.process_email(current_email)

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

        # Process recent emails
        recent_emails_analysis = []
        for email in email_request.recent_emails:
            thread = IngestedThread(
                thread_id=email.thread_id or "",
                latest_snippet=email.snippet or "",
                participants=[email.sender] + (email.recipients or []),
                received_at=datetime.fromisoformat(email.timestamp.replace('Z', '+00:00')),
                full_messages=[EmailMessage(
                    id="recent",
                    from_address=email.sender,
                    to_addresses=email.recipients or [],
                    date=datetime.fromisoformat(email.timestamp.replace('Z', '+00:00')),
                    subject=email.subject,
                    snippet=email.snippet or "",
                    body=email.body or email.snippet or ""
                )],
                subject=email.subject
            )
            all_threads.append(thread.to_dict())
            
            # Add basic analysis for each recent email
            recent_emails_analysis.append({
                "subject": email.subject,
                "sender": email.sender,
                "snippet": email.snippet,
                "timestamp": email.timestamp,
                "sentiment": "positive" if any(word in (email.body or email.snippet or "").lower() 
                                            for word in ["thank", "great", "appreciate"]) else "neutral",
                "urgency": "high" if any(word in email.subject.lower() 
                                       for word in ["urgent", "asap", "important"]) else "normal"
            })

        # Get bucket analysis from observer agent
        buckets = observer_agent.suggest_buckets(all_threads)
        bucket_assignments = observer_agent.assign_threads_to_buckets(all_threads, buckets)
        
        # Get user traits analysis
        user_traits = observer_agent.update_user_memory(all_threads)
        
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

        # Combine all analyses
        return EmailAnalysis(
            primary_intent=current_email_analysis["primary_intent"] if current_email_analysis else None,
            priority=current_email_analysis["priority"] if current_email_analysis else None,
            social_context=current_email_analysis["social_context"] if current_email_analysis else [],
            suggested_actions=current_email_analysis["suggested_actions"] if current_email_analysis else [],
            related_emails=current_email_analysis["related_emails"] if current_email_analysis else [],
            bucket=bucket_assignments.get(all_threads[0]['thread_id']) if all_threads else None,
            user_traits=user_traits["userTraits"],
            thread_summary=all_threads[0]['latest_snippet'] if all_threads else None,
            participants_analysis={
                "sender": email_request.current_email.sender if email_request.current_email else None,
                "recipients": email_request.current_email.recipients if email_request.current_email else [],
                "total_participants": len(email_request.current_email.recipients) + 1 if email_request.current_email else 0
            } if email_request.current_email else None,
            sentiment=current_email_analysis.get("sentiment", "neutral") if current_email_analysis else None,
            urgency=current_email_analysis.get("urgency", "normal") if current_email_analysis else None,
            follow_up_needed=current_email_analysis.get("follow_up_needed", False) if current_email_analysis else None,
            suggested_response=current_email_analysis.get("suggested_response") if current_email_analysis else None,
            available_buckets=available_buckets,
            threads=thread_list,
            recent_emails_analysis=recent_emails_analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 