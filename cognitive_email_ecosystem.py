import datetime
from typing import Dict, List, Optional, Set, Tuple
import json

class Email:
    """Representation of an email with metadata."""
    def __init__(self, sender: str, recipients: List[str], 
                 subject: str, body: str, timestamp: datetime.datetime,
                 thread_id: Optional[str] = None):
        self.sender = sender
        self.recipients = recipients
        self.subject = subject
        self.body = body
        self.timestamp = timestamp
        self.thread_id = thread_id
        self.processed = False
        self.metadata = {}  # Will store agent annotations

class ObserverAgent:
    """
    Top-level agent that maintains a mental model of user behavior patterns.
    Acts as the "prefrontal cortex" of the system.
    """
    def __init__(self):
        self.user_patterns = {
            'response_times': {},  # Map of sender -> avg response time
            'attention_periods': [],  # When user typically processes emails
            'priority_contacts': set(),  # Contacts that get quick responses
            'ignored_patterns': [],  # Patterns user tends to ignore
        }
        self.historical_decisions = []
    
    def observe_user_action(self, email: Email, action: str, timestamp: datetime.datetime):
        """Record user actions to improve the mental model."""
        if action == "replied":
            # Update response time patterns for this sender
            sender = email.sender
            response_time = (timestamp - email.timestamp).total_seconds() / 3600  # hours
            
            if sender in self.user_patterns['response_times']:
                # Moving average
                current_avg = self.user_patterns['response_times'][sender]
                self.user_patterns['response_times'][sender] = 0.8 * current_avg + 0.2 * response_time
            else:
                self.user_patterns['response_times'][sender] = response_time
                
            # If user responds quickly, consider this a priority contact
            if response_time < 1.0:  # Less than 1 hour
                self.user_patterns['priority_contacts'].add(sender)
                
        # Record decision for learning
        self.historical_decisions.append({
            'email_id': id(email),
            'action': action,
            'timestamp': timestamp
        })
    
    def predict_priority(self, email: Email) -> float:
        """
        Predict the priority level of an email based on learned patterns.
        Returns a value from 0.0 (lowest) to 1.0 (highest).
        """
        score = 0.5  # Default middle priority
        
        # Adjust based on sender relationship
        if email.sender in self.user_patterns['priority_contacts']:
            score += 0.3
            
        # Adjust based on thread importance
        if email.thread_id and any(d['email_id'] == id(e) and d['action'] == 'replied' 
                                for d in self.historical_decisions 
                                for e in [e for e in self.historical_decisions if e.thread_id == email.thread_id]):
            score += 0.2
            
        return min(score, 1.0)  # Cap at 1.0

class ContextAgent:
    """
    Analyzes external context factors like calendar, time, location.
    Acts as the "situational awareness" component.
    """
    def __init__(self):
        self.calendar_events = []
        self.current_location = None
        self.current_device = None
        self.current_focus_mode = "normal"
        
    def update_context(self, calendar_events, location=None, device=None, focus_mode=None):
        """Update the current context with new information."""
        self.calendar_events = calendar_events
        if location:
            self.current_location = location
        if device:
            self.current_device = device
        if focus_mode:
            self.current_focus_mode = focus_mode
    
    def get_current_availability(self) -> float:
        """Return user's estimated availability (0.0 to 1.0)."""
        now = datetime.datetime.now()
        
        # Check if user is in a meeting
        for event in self.calendar_events:
            if event['start'] <= now <= event['end']:
                if event.get('busy', True):
                    return 0.1  # Very low availability during meetings
                else:
                    return 0.4  # Higher but still limited during "free" calendar slots
        
        # Adjust based on focus mode
        if self.current_focus_mode == "do_not_disturb":
            return 0.2
        elif self.current_focus_mode == "focused_work":
            return 0.3
        
        # Default high availability
        return 0.9
        
    def contextualize_email(self, email: Email) -> None:
        """Add contextual metadata to the email."""
        # Add availability context
        email.metadata['user_availability'] = self.get_current_availability()
        
        # Check if email relates to imminent calendar events
        for event in self.calendar_events:
            event_start = event['start']
            time_until_event = (event_start - datetime.datetime.now()).total_seconds() / 3600
            
            if time_until_event < 2 and (
                event['title'].lower() in email.subject.lower() or 
                any(attendee in email.sender for attendee in event.get('attendees', []))
            ):
                email.metadata['related_imminent_event'] = event['title']
                email.metadata['context_urgency_boost'] = True

class SocialGraphAgent:
    """
    Maps and understands social relationships in the email network.
    Acts as the "social intelligence" component.
    """
    def __init__(self):
        self.connections = {}  # person -> set of people they communicate with
        self.org_hierarchy = {}  # person -> their manager
        self.teams = {}  # team name -> list of members
        self.communication_frequency = {}  # (person1, person2) -> count
        
    def add_communication(self, sender: str, recipients: List[str]):
        """Record a communication between people to build the social graph."""
        if sender not in self.connections:
            self.connections[sender] = set()
            
        for recipient in recipients:
            self.connections[sender].add(recipient)
            
            if recipient not in self.connections:
                self.connections[recipient] = set()
            self.connections[recipient].add(sender)
            
            # Track communication frequency
            pair = tuple(sorted([sender, recipient]))
            self.communication_frequency[pair] = self.communication_frequency.get(pair, 0) + 1
    
    def set_org_data(self, hierarchy: Dict[str, str], teams: Dict[str, List[str]]):
        """Set organizational data."""
        self.org_hierarchy = hierarchy
        self.teams = teams
    
    def analyze_social_context(self, email: Email) -> None:
        """Analyze the social context of an email and add metadata."""
        # Check organizational relationship
        if email.sender in self.org_hierarchy:
            manager = self.org_hierarchy[email.sender]
            if manager == "user_email":  # If sender reports to the user
                email.metadata['org_relationship'] = "direct_report"
            elif email.sender == self.org_hierarchy.get("user_email"):  # If sender is user's manager
                email.metadata['org_relationship'] = "manager"
                email.metadata['social_importance'] = "high"
        
        # Check team membership
        for team_name, members in self.teams.items():
            if email.sender in members and "user_email" in members:
                email.metadata['shared_team'] = team_name
                
        # Check communication frequency
        pair = tuple(sorted([email.sender, "user_email"]))
        frequency = self.communication_frequency.get(pair, 0)
        
        if frequency > 20:
            email.metadata['communication_frequency'] = "high"
        elif frequency > 5:
            email.metadata['communication_frequency'] = "medium"
        else:
            email.metadata['communication_frequency'] = "low"
            
            # If low frequency but connected to high-frequency contacts, mark as potentially important
            sender_connections = self.connections.get(email.sender, set())
            high_freq_connections = [
                contact for contact in sender_connections
                if self.communication_frequency.get(tuple(sorted([contact, "user_email"])), 0) > 20
            ]
            
            if high_freq_connections:
                email.metadata['network_importance'] = "potential_bridge"
                email.metadata['connected_via'] = high_freq_connections

class IntentDecoder:
    """
    Determines the underlying intent behind an email.
    Acts as the "empathy" component that understands communication purposes.
    """
    def __init__(self):
        # Simple keyword-based approach for prototype
        # In real implementation, this would use an LLM or specialized model
        self.intent_patterns = {
            'request_action': ['please', 'request', 'action', 'need you to', 'could you', 'by when'],
            'provide_info': ['fyi', 'just so you know', 'wanted to share', 'attached is'],
            'seek_input': ['what do you think', 'your thoughts', 'feedback', 'input', 'opinion'],
            'approval': ['approve', 'permission', 'sign off', 'go ahead', 'authorization'],
            'escalation': ['urgent', 'asap', 'emergency', 'critical', 'immediately'],
            'scheduling': ['meeting', 'calendar', 'availability', 'schedule', 'time to meet'],
        }
    
    def decode_intent(self, email: Email) -> None:
        """Analyze email to determine its intent and add as metadata."""
        body_lower = email.body.lower()
        subject_lower = email.subject.lower()
        
        # Calculate intent match scores
        intent_scores = {}
        for intent, keywords in self.intent_patterns.items():
            score = sum(2 if kw in subject_lower else 1 if kw in body_lower else 0 
                        for kw in keywords)
            if score > 0:
                intent_scores[intent] = score
        
        # Assign primary and secondary intents
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_intents:
            email.metadata['primary_intent'] = sorted_intents[0][0]
            if len(sorted_intents) > 1:
                email.metadata['secondary_intent'] = sorted_intents[1][0]
        else:
            email.metadata['primary_intent'] = 'unknown'
        
        # Add urgency determination
        email.metadata['intent_urgency'] = 'high' if 'escalation' in intent_scores else (
            'medium' if email.metadata['primary_intent'] in ['request_action', 'approval'] else 'low'
        )

class ExecutionSpecialist:
    """
    Task-specific agent that handles a particular type of email.
    Acts as the "motor cortex" that executes specific actions.
    """
    def __init__(self, specialty: str):
        self.specialty = specialty  # e.g., 'meeting_scheduler', 'information_gatherer', etc.
        self.action_templates = {}
        
    def can_handle(self, email: Email) -> bool:
        """Determine if this specialist can handle the given email."""
        primary_intent = email.metadata.get('primary_intent')
        
        if self.specialty == 'meeting_scheduler' and primary_intent == 'scheduling':
            return True
        elif self.specialty == 'approval_processor' and primary_intent == 'approval':
            return True
        elif self.specialty == 'information_gatherer' and primary_intent == 'seek_input':
            return True
        elif self.specialty == 'action_tracker' and primary_intent == 'request_action':
            return True
        elif self.specialty == 'emergency_handler' and email.metadata.get('intent_urgency') == 'high':
            return True
            
        return False
    
    def generate_action_plan(self, email: Email) -> Dict:
        """Generate an action plan for handling the email."""
        if not self.can_handle(email):
            return {"action": "escalate_to_user", "reason": "Outside specialist domain"}
            
        action_plan = {
            "email_id": id(email),
            "specialist": self.specialty,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        # Specific logic based on specialty
        if self.specialty == 'meeting_scheduler':
            action_plan.update({
                "action": "propose_meeting_times",
                "proposed_times": ["Extract times from calendar here"],
                "context": f"Based on your availability in the next week"
            })
        elif self.specialty == 'approval_processor':
            action_plan.update({
                "action": "prepare_approval_response",
                "approval_type": "standard",
                "relevant_details": ["Extract key details requiring approval"],
                "suggested_response": "Draft approval language here"
            })
        elif self.specialty == 'emergency_handler':
            action_plan.update({
                "action": "immediate_notification",
                "notification_channel": "mobile_alert",
                "urgency_factors": ["List reasons this is urgent"]
            })
            
        return action_plan

class CognitiveEmailSystem:
    """
    Main system that coordinates all agents in the cognitive email ecosystem.
    """
    def __init__(self):
        self.observer = ObserverAgent()
        self.context_agent = ContextAgent()
        self.social_graph = SocialGraphAgent()
        self.intent_decoder = IntentDecoder()
        self.specialists = [
            ExecutionSpecialist('meeting_scheduler'),
            ExecutionSpecialist('approval_processor'),
            ExecutionSpecialist('information_gatherer'),
            ExecutionSpecialist('action_tracker'),
            ExecutionSpecialist('emergency_handler'),
        ]
        self.processed_emails = []
        
    def process_email(self, email: Email) -> Dict:
        """Process an incoming email through the entire agent hierarchy."""
        # Step 1: Context analysis
        self.context_agent.contextualize_email(email)
        
        # Step 2: Social graph analysis
        self.social_graph.add_communication(email.sender, email.recipients)
        self.social_graph.analyze_social_context(email)
        
        # Step 3: Intent decoding
        self.intent_decoder.decode_intent(email)
        
        # Step 4: Priority prediction from observer
        priority = self.observer.predict_priority(email)
        email.metadata['predicted_priority'] = priority
        
        # Step 5: Find appropriate specialist
        suitable_specialists = [s for s in self.specialists if s.can_handle(email)]
        
        response = {
            "email_id": id(email),
            "metadata": email.metadata,
            "predicted_priority": priority,
        }
        
        # Step 6: Generate action plan if specialists available
        if suitable_specialists:
            specialist = suitable_specialists[0]  # Choose the first suitable specialist
            action_plan = specialist.generate_action_plan(email)
            response["action_plan"] = action_plan
            response["handling"] = "automated"
        else:
            response["handling"] = "manual"
            response["reason"] = "No suitable specialist available"
        
        # Mark as processed and store
        email.processed = True
        self.processed_emails.append(email)
        
        return response
    
    def record_user_action(self, email_id: int, action: str):
        """Record an action the user took on an email."""
        for email in self.processed_emails:
            if id(email) == email_id:
                self.observer.observe_user_action(email, action, datetime.datetime.now())
                break

# Example usage
if __name__ == "__main__":
    # Initialize the system
    system = CognitiveEmailSystem()
    
    # Set up some context
    system.context_agent.update_context(
        calendar_events=[{
            'title': 'Project Alpha Review',
            'start': datetime.datetime.now() + datetime.timedelta(hours=1),
            'end': datetime.datetime.now() + datetime.timedelta(hours=2),
            'attendees': ['manager@company.com', 'team1@company.com']
        }],
        location="Office",
        focus_mode="normal"
    )
    
    # Set up organization data
    system.social_graph.set_org_data(
        hierarchy={
            'manager@company.com': 'executive@company.com',
            'user_email': 'manager@company.com',
            'team1@company.com': 'user_email',
            'team2@company.com': 'user_email',
        },
        teams={
            'Project Alpha': ['user_email', 'team1@company.com', 'design@company.com'],
            'Project Beta': ['user_email', 'team2@company.com', 'external@partner.com'],
        }
    )
    
    # Create a sample email
    email = Email(
        sender='team1@company.com',
        recipients=['user_email'],
        subject='Urgent: Project Alpha budget approval needed',
        body='Hi, we need your approval on the revised budget for Project Alpha. The design team encountered a technical blocker that requires additional resources. Can you review and approve by EOD?',
        timestamp=datetime.datetime.now() - datetime.timedelta(minutes=30)
    )
    
    # Process the email
    result = system.process_email(email)
    
    # Print the result
    print(json.dumps(result, indent=2)) 