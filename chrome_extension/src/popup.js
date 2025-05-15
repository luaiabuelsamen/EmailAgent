// Simple state tracking
let currentEmailId = null;

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', () => {
    console.log('Popup loaded');
    showLoading();
    requestAnalysis();
});

// Request analysis for current email
function requestAnalysis() {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        const currentTab = tabs[0];
        if (!currentTab) {
            showError('No email selected');
            return;
        }

        currentEmailId = currentTab.url.split('/').pop();
        console.log('Requesting analysis for:', currentEmailId);
        
        chrome.runtime.sendMessage({
            type: 'ANALYZE_EMAIL',
            emailId: currentEmailId
        }, (response) => {
            console.log('Received response:', response);
            if (chrome.runtime.lastError) {
                showError(chrome.runtime.lastError.message);
                return;
            }
            
            if (response.error) {
                showError(response.error);
                return;
            }
            
            updateUI(response);
        });
    });
}

// Update UI with analysis results
function updateUI(analysis) {
    console.log('Updating UI with:', analysis);
    
    // Remove loading state
    hideLoading();
    
    try {
        // Primary intent and priority
        setText('primary-intent', `Primary Intent: ${analysis.primary_intent || 'Unknown'}`);
        setText('priority', `Priority: ${analysis.priority || 'Normal'}`);
        
        // Social context
        const socialContext = document.getElementById('social-context');
        if (socialContext) {
            if (Array.isArray(analysis.social_context) && analysis.social_context.length > 0) {
                socialContext.innerHTML = `
                    <ul>
                        ${analysis.social_context.map(context => `<li>${context}</li>`).join('')}
                    </ul>
                `;
            } else {
                socialContext.innerHTML = '<span class="no-data">No social context available</span>';
            }
        }
        
        // Suggested actions
        const suggestedActions = document.getElementById('suggested-actions');
        if (suggestedActions) {
            if (Array.isArray(analysis.suggested_actions) && analysis.suggested_actions.length > 0) {
                suggestedActions.innerHTML = `
                    <ul>
                        ${analysis.suggested_actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                `;
            } else {
                suggestedActions.innerHTML = '<span class="no-data">No suggested actions available</span>';
            }
        }
        
        // Related emails
        const relatedEmails = document.getElementById('related-emails');
        if (relatedEmails) {
            if (Array.isArray(analysis.related_emails) && analysis.related_emails.length > 0) {
                relatedEmails.innerHTML = `
                    <ul>
                        ${analysis.related_emails
                            .map(email => `<li>${email.subject || 'No subject'} (${email.sender || 'Unknown sender'})</li>`)
                            .join('')}
                    </ul>
                `;
            } else {
                relatedEmails.innerHTML = '<span class="no-data">No related emails available</span>';
            }
        }
    } catch (error) {
        console.error('Error updating UI:', error);
        showError('Error displaying analysis results. Please try again.');
    }
}

// Helper functions
function setText(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = text;
    }
}

function showLoading() {
    const loading = document.querySelector('.loading');
    if (loading) {
        loading.style.display = 'block';
    }
}

function hideLoading() {
    const loading = document.querySelector('.loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

function showError(message) {
    hideLoading();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    document.body.insertBefore(errorDiv, document.body.firstChild);
}

async function updateTabContent(tabId) {
    if (!currentEmailId) return;

    const contentBox = document.querySelector(`#${tabId} .analysis-box`);
    contentBox.innerHTML = '<div class="loading"></div>';

    try {
        const analysis = await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({
                type: 'ANALYZE_EMAIL',
                emailId: currentEmailId
            }, (response) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    resolve(response);
                }
            });
        });

        // Update the content based on the tab
        switch (tabId) {
            case 'sentiment':
                contentBox.innerHTML = `
                    <h3>Sentiment Analysis</h3>
                    <div class="sentiment-result">
                        <p class="sentiment-label">Primary Intent:</p>
                        <p class="sentiment-value">${analysis.primary_intent || 'Unknown'}</p>
                        <p class="confidence">Priority: ${analysis.priority || 'Normal'}</p>
                    </div>
                `;
                break;
            case 'summary':
                contentBox.innerHTML = `
                    <h3>Email Summary</h3>
                    <div class="summary-content">
                        <p>${analysis.social_context?.join('. ') || 'No summary available'}</p>
                    </div>
                `;
                break;
            case 'suggestions':
                contentBox.innerHTML = `
                    <h3>Writing Suggestions</h3>
                    <div class="suggestions-list">
                        <ul>
                            ${analysis.suggested_actions?.map(action => 
                                `<li>${action}</li>`
                            ).join('') || '<li>No suggestions available</li>'}
                        </ul>
                    </div>
                `;
                break;
        }
    } catch (error) {
        console.error('Error updating tab content:', error);
        contentBox.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
} 