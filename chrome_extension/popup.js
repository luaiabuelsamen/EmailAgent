document.addEventListener('DOMContentLoaded', async () => {
    const loading = document.getElementById('loading');
    const analysis = document.getElementById('analysis');
    const copyButton = document.getElementById('copy-response');

    // Tab handling
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    try {
        // Get the current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab.url.includes('mail.google.com')) {
            showError('Please open this extension on a Gmail page');
            return;
        }

        // Send message to content script to get email data
        const response = await chrome.tabs.sendMessage(tab.id, { action: 'getEmailContent' });
        
        if (!response.success) {
            showError('Failed to get email content');
            return;
        }

        // Send email data to backend for analysis
        const analysisResponse = await fetch('http://localhost:8000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(response.data)
        });

        if (!analysisResponse.ok) {
            throw new Error('Failed to analyze email');
        }

        const analysisData = await analysisResponse.json();
        
        // Update UI with analysis results
        updateUI(analysisData, response.data);
        
        // Hide loading, show analysis
        loading.style.display = 'none';
        analysis.style.display = 'block';

    } catch (error) {
        showError(error.message);
    }
});

function updateUI(analysis, emailData) {
    // Overview tab
    if (emailData.current_email) {
        document.getElementById('primary-intent').textContent = analysis.primary_intent || 'No intent detected';
        document.getElementById('priority').textContent = analysis.priority || 'NORMAL';
        document.getElementById('urgency').textContent = analysis.urgency || 'NORMAL';
        document.getElementById('bucket').textContent = analysis.bucket || 'Uncategorized';
        document.getElementById('sentiment').textContent = analysis.sentiment || 'Neutral';
    }

    // Buckets tab
    const bucketsContainer = document.getElementById('email-buckets');
    if (analysis.available_buckets) {
        bucketsContainer.innerHTML = analysis.available_buckets.map(bucket => `
            <div class="bucket-card ${bucket.name === analysis.bucket ? 'active' : ''}">
                <div class="title">${bucket.name}</div>
                <div class="description">${bucket.description}</div>
                <div class="count">${bucket.count} emails</div>
            </div>
        `).join('');
    }

    // Recent Emails tab
    const recentEmailsList = document.getElementById('recent-emails');
    if (analysis.recent_emails_analysis) {
        recentEmailsList.innerHTML = analysis.recent_emails_analysis.map(email => `
            <div class="email-item">
                <div class="email-header">
                    <div class="email-subject">${email.subject}</div>
                    <div class="email-meta">
                        <span class="email-sender">${email.sender}</span>
                        <span class="email-time">${formatDate(email.timestamp)}</span>
                    </div>
                </div>
                <div class="email-snippet">${email.snippet}</div>
                <div class="email-tags">
                    <span class="tag ${email.urgency}-tag">${email.urgency.toUpperCase()}</span>
                    <span class="tag sentiment-tag">${email.sentiment}</span>
                </div>
            </div>
        `).join('');
    }

    // Details tab
    if (emailData.current_email) {
        document.getElementById('email-subject').textContent = emailData.current_email.subject || 'No Subject';
        document.getElementById('email-body').textContent = emailData.current_email.body || 'No Content';

        // Social Context section
        const socialContext = document.getElementById('social-context');
        socialContext.innerHTML = analysis.social_context
            .map(context => `<span class="tag">${context}</span>`)
            .join('');

        // Participants section
        const participants = document.getElementById('participants');
        if (analysis.participants_analysis) {
            participants.innerHTML = `
                <div class="participant">
                    <span class="participant-role">From:</span>
                    ${analysis.participants_analysis.sender}
                </div>
                <div class="participant">
                    <span class="participant-role">To:</span>
                    ${analysis.participants_analysis.recipients.join(', ')}
                </div>
            `;
        }

        // Actions tab
        const suggestedActions = document.getElementById('suggested-actions');
        suggestedActions.innerHTML = analysis.suggested_actions
            .map(action => `<button class="action-button">${action}</button>`)
            .join('');

        document.getElementById('suggested-response').textContent = analysis.suggested_response || '';

        // Add copy button functionality
        document.getElementById('copy-response').addEventListener('click', () => {
            const response = analysis.suggested_response;
            if (response) {
                navigator.clipboard.writeText(response)
                    .then(() => {
                        const button = document.getElementById('copy-response');
                        const originalText = button.textContent;
                        button.textContent = 'Copied!';
                        setTimeout(() => {
                            button.textContent = originalText;
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Failed to copy text: ', err);
                    });
            }
        });
    }
}

function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
        return 'Yesterday';
    } else if (days < 7) {
        return date.toLocaleDateString([], { weekday: 'short' });
    } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
}

function showError(message) {
    const loading = document.getElementById('loading');
    loading.textContent = `Error: ${message}`;
    loading.style.color = 'red';
} 