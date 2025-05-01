from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import anthropic
from src.cognitive_email_adapter import CognitiveEmailAdapter
from config import ANTHROPIC_API_KEY, CORS_ORIGINS, BACKEND_PORT
import json

app = FastAPI()

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Enable CORS for the Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the cognitive email adapter
adapter = CognitiveEmailAdapter()

class EmailAnalysisRequest(BaseModel):
    email: dict
    context: dict

class EmailAnalysisResponse(BaseModel):
    primaryIntent: str
    priority: str
    socialContext: List[str]
    suggestions: List[str]
    relatedEmails: Optional[List[dict]] = None

@app.post("/analyze-email", response_model=EmailAnalysisResponse)
async def analyze_email(request: EmailAnalysisRequest):
    try:
        # Convert the email data to the format expected by the cognitive system
        email_data = {
            "id": request.email.get("emailId"),
            "from": request.email.get("from"),
            "to": request.email.get("to", []),
            "cc": request.email.get("cc", []),
            "date": request.email.get("timestamp"),
            "subject": request.email.get("subject"),
            "snippet": request.email.get("body", "")[:100],
            "body": request.email.get("body", "")
        }
        
        # Create an EmailMessage object
        email_message = adapter.ingestion_agent.EmailMessage.from_dict(email_data)
        
        # Create an IngestedThread with a single message
        thread = adapter.ingestion_agent.IngestedThread(
            thread_id=email_data["id"],
            latest_snippet=email_data["snippet"],
            participants=[email_data["from"]] + email_data["to"] + email_data["cc"],
            received_at=datetime.datetime.fromisoformat(email_data["date"].replace('Z', '+00:00')),
            full_messages=[email_message],
            subject=email_data["subject"]
        )
        
        # Process the thread through the cognitive system
        adapter.initialize_system()
        emails = adapter.convert_to_cognitive_email(thread)
        
        if not emails:
            raise HTTPException(status_code=400, detail="Failed to process email")
            
        # Get the analysis result
        result = adapter.cognitive_system.process_email(emails[0])
        
        # Enhance analysis with Anthropic
        enhanced_analysis = await enhance_analysis_with_anthropic(result, email_data)
        
        # Convert the result to the format expected by the extension
        response = EmailAnalysisResponse(
            primaryIntent=enhanced_analysis.get("primary_intent", "unknown"),
            priority=enhanced_analysis.get("priority", "medium").capitalize(),
            socialContext=enhanced_analysis.get("social_context", []),
            suggestions=enhanced_analysis.get("suggested_actions", []),
            relatedEmails=enhanced_analysis.get("related_emails", [])
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def enhance_analysis_with_anthropic(analysis: dict, email_data: dict) -> dict:
    """Enhance the analysis using Anthropic's Claude model."""
    try:
        # Prepare the prompt for Claude
        prompt = f"""
        Analyze this email and enhance the provided analysis:
        
        Email Subject: {email_data['subject']}
        From: {email_data['from']}
        To: {', '.join(email_data['to'])}
        CC: {', '.join(email_data['cc'])}
        Body: {email_data['body']}
        
        Current Analysis:
        - Primary Intent: {analysis.get('primary_intent', 'unknown')}
        - Priority: {analysis.get('priority', 'medium')}
        - Social Context: {', '.join(analysis.get('social_context', []))}
        - Suggested Actions: {', '.join(analysis.get('suggested_actions', []))}
        
        Please provide an enhanced analysis focusing on:
        1. More nuanced understanding of the email's intent
        2. Better prioritization based on content and context
        3. More detailed social context analysis
        4. More specific and actionable suggestions
        
        Format your response as a JSON object with these fields:
        - primary_intent: string
        - priority: string (high/medium/low)
        - social_context: array of strings
        - suggested_actions: array of strings
        - related_emails: array of objects with subject and from fields
        """
        
        # Call Claude
        response = await anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse the response
        enhanced_analysis = json.loads(response.content[0].text)
        return enhanced_analysis
        
    except Exception as e:
        print(f"Error enhancing analysis with Anthropic: {e}")
        return analysis  # Return original analysis if enhancement fails

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BACKEND_PORT) 