import datetime
import json
from flask import Flask, render_template_string, request, jsonify
from cognitive_email_ecosystem import CognitiveEmailSystem, Email

app = Flask(__name__)

# Initialize the cognitive email system
system = CognitiveEmailSystem()

# Set up some sample data
def initialize_sample_data():
    # Set up context data
    system.context_agent.update_context(
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
    
    # Set up organizational data
    system.social_graph.set_org_data(
        hierarchy={
            'manager@company.com': 'executive@company.com',
            'user_email': 'manager@company.com',
            'team1@company.com': 'user_email',
            'team2@company.com': 'user_email',
            'design@company.com': 'user_email',
            'external@partner.com': 'partner_manager@partner.com',
        },
        teams={
            'Project Alpha': ['user_email', 'team1@company.com', 'design@company.com'],
            'Project Beta': ['user_email', 'team2@company.com', 'external@partner.com'],
        }
    )

    # Create some sample emails
    sample_emails = [
        Email(
            sender='team1@company.com',
            recipients=['user_email'],
            subject='Urgent: Project Alpha budget approval needed',
            body='Hi, we need your approval on the revised budget for Project Alpha. The design team encountered a technical blocker that requires additional resources. Can you review and approve by EOD?',
            timestamp=datetime.datetime.now() - datetime.timedelta(minutes=30),
            thread_id='thread1'
        ),
        Email(
            sender='manager@company.com',
            recipients=['user_email', 'team1@company.com'],
            subject='Quarterly Goals Review',
            body='Let\'s schedule time next week to review progress on our quarterly goals. What times work for you?',
            timestamp=datetime.datetime.now() - datetime.timedelta(hours=2),
            thread_id='thread2'
        ),
        Email(
            sender='external@partner.com',
            recipients=['user_email'],
            subject='FYI: New API Documentation',
            body='Just wanted to share the updated API documentation for the integration we discussed last week. No action needed, just for your information.',
            timestamp=datetime.datetime.now() - datetime.timedelta(hours=5),
            thread_id='thread3'
        ),
        Email(
            sender='newsletter@tech-news.com',
            recipients=['user_email'],
            subject='This Week in Tech: AI Breakthroughs',
            body='Here are this week\'s top stories in tech and AI development...',
            timestamp=datetime.datetime.now() - datetime.timedelta(days=1),
            thread_id='thread4'
        ),
        Email(
            sender='design@company.com',
            recipients=['user_email', 'team1@company.com'],
            subject='Project Alpha - Design Feedback Needed',
            body='I\'ve created some mockups for the new feature. What do you think about these designs? I especially need your feedback on the user flow.',
            timestamp=datetime.datetime.now() - datetime.timedelta(hours=3),
            thread_id='thread5'
        ),
        Email(
            sender='urgent@security.com',
            recipients=['user_email'],
            subject='URGENT: Security Alert',
            body='We\'ve detected unusual login activity on your account. Please verify this was you or secure your account immediately.',
            timestamp=datetime.datetime.now() - datetime.timedelta(minutes=15),
            thread_id='thread6'
        ),
    ]
    
    # Process sample emails
    processed_results = []
    for email in sample_emails:
        result = system.process_email(email)
        processed_results.append(result)
    
    return processed_results

# HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cognitive Email Ecosystem</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            display: flex;
        }
        header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            text-align: center;
        }
        .sidebar {
            width: 300px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
            margin-right: 20px;
        }
        .main-content {
            flex: 1;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 20px;
        }
        .email-list {
            margin-bottom: 20px;
        }
        .email-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .email-item:hover {
            background-color: #f9f9f9;
        }
        .email-item.selected {
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
        }
        .email-item h3 {
            margin: 0 0 5px;
            font-size: 16px;
            color: #333;
        }
        .email-item p {
            margin: 0;
            color: #666;
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .email-item .metadata {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        .intent-tag {
            display: inline-block;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
            margin-right: 5px;
            color: white;
        }
        .intent-tag.request_action { background-color: #F44336; }
        .intent-tag.provide_info { background-color: #4CAF50; }
        .intent-tag.seek_input { background-color: #2196F3; }
        .intent-tag.approval { background-color: #FF9800; }
        .intent-tag.escalation { background-color: #9C27B0; }
        .intent-tag.scheduling { background-color: #795548; }
        .intent-tag.unknown { background-color: #9E9E9E; }
        
        .priority-indicator {
            width: 8px;
            height: 40px;
            margin-right: 10px;
            border-radius: 4px;
        }
        .high-priority { background-color: #f44336; }
        .medium-priority { background-color: #ff9800; }
        .low-priority { background-color: #4caf50; }
        
        .cluster-header {
            padding: 10px 15px;
            background-color: #f5f7fa;
            font-weight: bold;
            border-left: 4px solid #2196F3;
            margin-bottom: 10px;
        }
        
        .email-detail {
            padding: 20px;
        }
        .email-detail .email-header {
            margin-bottom: 20px;
        }
        .email-detail .email-header h2 {
            margin: 0 0 10px;
        }
        .email-detail .email-header .metadata {
            display: flex;
            color: #666;
        }
        .email-detail .email-header .metadata div {
            margin-right: 20px;
        }
        .email-detail .email-body {
            line-height: 1.6;
            color: #333;
            margin-bottom: 30px;
        }
        .email-detail .agent-analysis {
            background-color: #f5f7fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .email-detail .agent-analysis h3 {
            margin-top: 0;
            color: #2196F3;
        }
        .action-panel {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .action-panel h3 {
            margin-top: 0;
            color: #2196F3;
        }
        .btn {
            display: inline-block;
            padding: 8px 15px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }
        .btn:hover {
            background-color: #0d8bf0;
        }
        .stats-panel {
            margin-bottom: 30px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .flex-row {
            display: flex;
            align-items: center;
        }
    </style>
</head>
<body>
    <header>
        <h1>Cognitive Email Ecosystem</h1>
        <p>A Hierarchical Agent Approach to Email Management</p>
    </header>
    
    <div class="container">
        <div class="sidebar">
            <div class="stats-panel">
                <h2>Agent Context</h2>
                <div class="stat-item">
                    <span>Current Availability:</span>
                    <span>{{ availability * 100 }}%</span>
                </div>
                <div class="stat-item">
                    <span>Focus Mode:</span>
                    <span>{{ focus_mode }}</span>
                </div>
                <div class="stat-item">
                    <span>Upcoming:</span>
                    <span>{{ next_event }}</span>
                </div>
            </div>
            
            <h2>Smart Clusters</h2>
            <div class="email-list">
                <div class="cluster-header">High Priority ({{ high_priority_count }})</div>
                {% for email in high_priority_emails %}
                <div class="email-item {% if loop.first %}selected{% endif %}" onclick="showEmailDetail('{{ email.email_id }}')">
                    <div class="flex-row">
                        <div class="priority-indicator high-priority"></div>
                        <div>
                            <h3>{{ email.subject }}</h3>
                            <p>{{ email.sender }}</p>
                            <div class="metadata">
                                <span>{{ email.time_ago }}</span>
                                <span class="intent-tag {{ email.metadata.primary_intent }}">{{ email.metadata.primary_intent }}</span>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
                
                <div class="cluster-header">Project Alpha ({{ project_alpha_count }})</div>
                {% for email in project_alpha_emails %}
                <div class="email-item" onclick="showEmailDetail('{{ email.email_id }}')">
                    <div class="flex-row">
                        {% if email.metadata.predicted_priority > 0.7 %}
                        <div class="priority-indicator high-priority"></div>
                        {% elif email.metadata.predicted_priority > 0.4 %}
                        <div class="priority-indicator medium-priority"></div>
                        {% else %}
                        <div class="priority-indicator low-priority"></div>
                        {% endif %}
                        <div>
                            <h3>{{ email.subject }}</h3>
                            <p>{{ email.sender }}</p>
                            <div class="metadata">
                                <span>{{ email.time_ago }}</span>
                                <span class="intent-tag {{ email.metadata.primary_intent }}">{{ email.metadata.primary_intent }}</span>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
                
                <div class="cluster-header">Information Updates ({{ info_updates_count }})</div>
                {% for email in info_updates_emails %}
                <div class="email-item" onclick="showEmailDetail('{{ email.email_id }}')">
                    <div class="flex-row">
                        {% if email.metadata.predicted_priority > 0.7 %}
                        <div class="priority-indicator high-priority"></div>
                        {% elif email.metadata.predicted_priority > 0.4 %}
                        <div class="priority-indicator medium-priority"></div>
                        {% else %}
                        <div class="priority-indicator low-priority"></div>
                        {% endif %}
                        <div>
                            <h3>{{ email.subject }}</h3>
                            <p>{{ email.sender }}</p>
                            <div class="metadata">
                                <span>{{ email.time_ago }}</span>
                                <span class="intent-tag {{ email.metadata.primary_intent }}">{{ email.metadata.primary_intent }}</span>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="main-content">
            <div class="email-detail">
                {% if selected_email %}
                <div class="email-header">
                    <h2>{{ selected_email.subject }}</h2>
                    <div class="metadata">
                        <div><strong>From:</strong> {{ selected_email.sender }}</div>
                        <div><strong>To:</strong> {{ selected_email.recipients|join(', ') }}</div>
                        <div><strong>Sent:</strong> {{ selected_email.time_ago }}</div>
                    </div>
                </div>
                
                <div class="email-body">
                    {{ selected_email.body|replace('\n', '<br>') }}
                </div>
                
                {% if selected_email.handling == 'automated' %}
                <div class="action-panel">
                    <h3>Suggested Action</h3>
                    <p>{{ selected_email.action_description }}</p>
                    <button class="btn">Accept Suggestion</button>
                    <button class="btn">Modify</button>
                    <button class="btn">Handle Manually</button>
                </div>
                {% endif %}
                
                <div class="agent-analysis">
                    <h3>Cognitive Analysis</h3>
                    <div class="stat-item">
                        <span>Primary Intent:</span>
                        <span class="intent-tag {{ selected_email.metadata.primary_intent }}">{{ selected_email.metadata.primary_intent }}</span>
                    </div>
                    {% if selected_email.metadata.secondary_intent %}
                    <div class="stat-item">
                        <span>Secondary Intent:</span>
                        <span class="intent-tag {{ selected_email.metadata.secondary_intent }}">{{ selected_email.metadata.secondary_intent }}</span>
                    </div>
                    {% endif %}
                    <div class="stat-item">
                        <span>Predicted Priority:</span>
                        <span>{{ (selected_email.metadata.predicted_priority * 100)|int }}%</span>
                    </div>
                    {% if selected_email.metadata.org_relationship %}
                    <div class="stat-item">
                        <span>Relationship:</span>
                        <span>{{ selected_email.metadata.org_relationship }}</span>
                    </div>
                    {% endif %}
                    {% if selected_email.metadata.shared_team %}
                    <div class="stat-item">
                        <span>Shared Team:</span>
                        <span>{{ selected_email.metadata.shared_team }}</span>
                    </div>
                    {% endif %}
                    {% if selected_email.metadata.communication_frequency %}
                    <div class="stat-item">
                        <span>Communication Frequency:</span>
                        <span>{{ selected_email.metadata.communication_frequency }}</span>
                    </div>
                    {% endif %}
                    {% if selected_email.metadata.related_imminent_event %}
                    <div class="stat-item">
                        <span>Related Event:</span>
                        <span>{{ selected_email.metadata.related_imminent_event }}</span>
                    </div>
                    {% endif %}
                    {% if selected_email.metadata.context_urgency_boost %}
                    <div class="stat-item">
                        <span>Context Urgency:</span>
                        <span>Elevated due to imminent event</span>
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
        function showEmailDetail(emailId) {
            // In a real app, this would fetch email details via AJAX
            // For this demo, we'll just reload the page with a query parameter
            window.location.href = '/?email_id=' + emailId;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    # Initialize system with sample data if not already done
    if not system.processed_emails:
        email_results = initialize_sample_data()
    
    # Get selected email from query param
    email_id = request.args.get('email_id')
    selected_email = None
    
    # Prepare data for template
    email_data = []
    high_priority_emails = []
    project_alpha_emails = []
    info_updates_emails = []
    
    for email in system.processed_emails:
        # Calculate time ago string
        now = datetime.datetime.now()
        time_diff = now - email.timestamp
        
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} days ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        # Create a dictionary with email data for the template
        email_dict = {
            'email_id': id(email),
            'subject': email.subject,
            'sender': email.sender,
            'recipients': email.recipients,
            'body': email.body,
            'time_ago': time_ago,
            'metadata': email.metadata,
            'handling': 'manual'
        }
        
        # Check if this is the selected email
        if email_id and int(email_id) == id(email):
            selected_email = email_dict
            
            # Get action plan if available
            for result in system.processed_emails:
                if id(result) == int(email_id):
                    result_data = system.process_email(result)
                    if 'action_plan' in result_data:
                        email_dict['handling'] = 'automated'
                        
                        # Generate a human-readable action description
                        if result_data['action_plan']['specialist'] == 'approval_processor':
                            email_dict['action_description'] = 'I can prepare an approval response based on the budget details.'
                        elif result_data['action_plan']['specialist'] == 'meeting_scheduler':
                            email_dict['action_description'] = 'I can suggest meeting times based on your calendar availability.'
                        elif result_data['action_plan']['specialist'] == 'emergency_handler':
                            email_dict['action_description'] = 'This appears urgent - I can notify you immediately via mobile alert.'
                        else:
                            email_dict['action_description'] = f"I can handle this {email_dict['metadata']['primary_intent']} email automatically."
                    break
        
        # Categorize emails for smart clustering
        if 'intent_urgency' in email.metadata and email.metadata['intent_urgency'] == 'high':
            high_priority_emails.append(email_dict)
        
        if 'shared_team' in email.metadata and email.metadata['shared_team'] == 'Project Alpha':
            project_alpha_emails.append(email_dict)
        elif 'primary_intent' in email.metadata and email.metadata['primary_intent'] == 'provide_info':
            info_updates_emails.append(email_dict)
    
    # Sort emails by predicted priority within each cluster
    high_priority_emails.sort(key=lambda x: x['metadata'].get('predicted_priority', 0), reverse=True)
    project_alpha_emails.sort(key=lambda x: x['metadata'].get('predicted_priority', 0), reverse=True)
    info_updates_emails.sort(key=lambda x: x['metadata'].get('predicted_priority', 0), reverse=True)
    
    # Get next calendar event
    next_event = "No upcoming events"
    if system.context_agent.calendar_events:
        sorted_events = sorted(system.context_agent.calendar_events, key=lambda e: e['start'])
        for event in sorted_events:
            if event['start'] > datetime.datetime.now():
                next_event = f"{event['title']} in {((event['start'] - datetime.datetime.now()).seconds // 60)} min"
                break
    
    # Render template with data
    return render_template_string(HTML_TEMPLATE, 
        availability=system.context_agent.get_current_availability(),
        focus_mode=system.context_agent.current_focus_mode,
        next_event=next_event,
        high_priority_emails=high_priority_emails,
        high_priority_count=len(high_priority_emails),
        project_alpha_emails=project_alpha_emails,
        project_alpha_count=len(project_alpha_emails),
        info_updates_emails=info_updates_emails,
        info_updates_count=len(info_updates_emails),
        selected_email=selected_email
    )

if __name__ == '__main__':
    app.run(debug=True) 