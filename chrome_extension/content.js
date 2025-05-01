// Function to get the current email ID from Gmail's URL
function getCurrentEmailId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('message_id') || urlParams.get('id');
}

// Function to get the current thread ID from Gmail's URL
function getCurrentThreadId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('th') || urlParams.get('thread_id');
}

// Function to extract emails from Gmail's inbox list
function extractInboxEmails() {
    const tableRows = document.querySelectorAll('tr.zA');
    const emails = [];

    tableRows.forEach(row => {
        // Extract basic information visible in the inbox
        const subjectElement = row.querySelector('td.a4W');
        const senderElement = row.querySelector('td.yX span[email]');
        const snippetElement = row.querySelector('span.y2');
        const dateElement = row.querySelector('td.xW');

        if (subjectElement && senderElement) {
            emails.push({
                subject: subjectElement.textContent.trim(),
                sender: senderElement.getAttribute('email'),
                recipients: [], // Will be populated when email is opened
                snippet: snippetElement ? snippetElement.textContent.trim() : '',
                timestamp: dateElement ? dateElement.getAttribute('title') : new Date().toISOString(),
                thread_id: row.getAttribute('data-thread-id')
            });
        }
    });

    return emails.slice(0, 10); // Return only the last 10 emails
}

// Function to check if extension is connected
function isExtensionConnected() {
    return new Promise((resolve) => {
        try {
            console.log('Checking extension connection...');
            chrome.runtime.sendMessage({ type: 'PING' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('Connection error:', chrome.runtime.lastError);
                    resolve(false);
                } else {
                    console.log('PING response:', response);
                    resolve(response && response.connected === true);
                }
            });
        } catch (error) {
            console.error('Error checking connection:', error);
            resolve(false);
        }
    });
}

// Function to extract thread information
function extractThreadInfo() {
    const threadContainer = document.querySelector('div[role="main"]');
    if (!threadContainer) return null;

    const messages = Array.from(threadContainer.querySelectorAll('div[role="listitem"]'));
    const threadInfo = {
        thread_id: getCurrentThreadId(),
        messages: []
    };

    messages.forEach(message => {
        const senderElement = message.querySelector('span[email]');
        const recipientElements = message.querySelectorAll('span[email]:not(:first-child)');
        const bodyElement = message.querySelector('div[role="textbox"]');
        const timestampElement = message.querySelector('time');

        if (senderElement) {
            threadInfo.messages.push({
                sender: senderElement.getAttribute('email'),
                recipients: Array.from(recipientElements).map(el => el.getAttribute('email')),
                body: bodyElement ? bodyElement.innerText.trim() : '',
                timestamp: timestampElement ? timestampElement.getAttribute('datetime') : new Date().toISOString()
            });
        }
    });

    return threadInfo;
}

// Function to extract email content from Gmail's DOM
function extractEmailContent() {
    // Check if we're in Gmail
    if (!window.location.hostname.includes('mail.google.com')) {
        throw new Error('Not in Gmail');
    }

    // If we're viewing a specific email
    if (getCurrentEmailId()) {
        // Find the email container
        const emailContainer = document.querySelector('div[role="main"]');
        if (!emailContainer) {
            throw new Error('Email container not found');
        }

        // Extract email subject
        const subjectElement = emailContainer.querySelector('h2');
        const subject = subjectElement ? subjectElement.textContent.trim() : '';

        // Extract sender information
        const senderElement = emailContainer.querySelector('span[email]');
        const sender = senderElement ? senderElement.getAttribute('email') : '';

        // Extract recipients
        const recipientElements = emailContainer.querySelectorAll('span[email]:not(:first-child)');
        const recipients = Array.from(recipientElements).map(el => el.getAttribute('email'));

        // Extract email body
        const bodyElement = emailContainer.querySelector('div[role="textbox"]');
        const body = bodyElement ? bodyElement.innerText.trim() : '';

        // Get thread information
        const threadInfo = extractThreadInfo();

        return {
            current_email: {
                subject,
                sender,
                recipients,
                body,
                timestamp: new Date().toISOString(),
                thread_id: getCurrentThreadId(),
                thread_info: threadInfo
            },
            recent_emails: extractInboxEmails()
        };
    } else {
        // If we're on the inbox view
        return {
            current_email: null,
            recent_emails: extractInboxEmails()
        };
    }
}

// Function to analyze email content
async function analyzeEmail(emailData) {
    console.log('Starting email analysis...');
    
    try {
        // Check if extension is connected
        const connected = await isExtensionConnected();
        if (!connected) {
            console.error('Extension not connected');
            return;
        }

        // Send email content to background script for analysis
        chrome.runtime.sendMessage({
            type: 'GET_EMAIL',
            emailData: emailData
        }, response => {
            if (chrome.runtime.lastError) {
                console.error('Error sending message:', chrome.runtime.lastError);
                return;
            }
            
            console.log('Received analysis response:', response);
            
            if (response && response.success) {
                updateUI(response.analysis);
            } else {
                console.error('Analysis failed:', response ? response.error : 'No response received');
            }
        });
    } catch (error) {
        console.error('Error in analyzeEmail:', error);
    }
}

// Function to update the UI with analysis results using Lovable
function updateUI(analysis) {
    console.log('Updating UI with analysis:', analysis);
    
    // Remove any existing analysis container
    const existingContainer = document.querySelector('.cognitive-email-analysis');
    if (existingContainer) {
        existingContainer.remove();
    }

    // Create new analysis container with Lovable styling
    const analysisContainer = document.createElement('div');
    analysisContainer.className = 'cognitive-email-analysis';
    analysisContainer.innerHTML = `
        <div class="lovable-card">
            <div class="lovable-header">
                <h3 class="lovable-title">Cognitive Analysis</h3>
                <div class="lovable-badge ${analysis.priority.toLowerCase()}">${analysis.priority}</div>
            </div>
            
            <div class="lovable-content">
                <div class="lovable-section">
                    <h4 class="lovable-subtitle">Primary Intent</h4>
                    <p class="lovable-text">${analysis.primaryIntent}</p>
                </div>
                
                <div class="lovable-section">
                    <h4 class="lovable-subtitle">Social Context</h4>
                    <div class="lovable-tags">
                        ${analysis.socialContext.map(context => `
                            <span class="lovable-tag">${context}</span>
                        `).join('')}
                    </div>
                </div>
                
                <div class="lovable-section">
                    <h4 class="lovable-subtitle">Suggested Actions</h4>
                    <div class="lovable-actions">
                        ${analysis.suggestions.map(suggestion => `
                            <button class="lovable-button">${suggestion}</button>
                        `).join('')}
                    </div>
                </div>
                
                ${analysis.relatedEmails ? `
                <div class="lovable-section">
                    <h4 class="lovable-subtitle">Related Emails</h4>
                    <div class="lovable-list">
                        ${analysis.relatedEmails.map(email => `
                            <div class="lovable-list-item">
                                <span class="lovable-list-title">${email.subject}</span>
                                <span class="lovable-list-meta">${email.from}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    // Insert analysis into Gmail's interface
    const emailHeader = document.querySelector('.ha');
    if (emailHeader) {
        emailHeader.parentNode.insertBefore(analysisContainer, emailHeader.nextSibling);
        console.log('Analysis UI added to page');
    } else {
        console.log('Could not find email header element');
    }
}

// Listen for Gmail's URL changes to detect when a new email is opened
let lastEmailId = null;
setInterval(() => {
    const currentEmailId = getCurrentEmailId();
    if (currentEmailId !== lastEmailId) {
        console.log('New email detected:', currentEmailId);
        lastEmailId = currentEmailId;
        const emailContent = extractEmailContent();
        if (emailContent) {
            analyzeEmail(emailContent);
        }
    }
}, 1000);

// Listen for messages from the extension
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Content script received message:', request);

    if (request.action === 'getEmailContent') {
        try {
            const emailContent = extractEmailContent();
            sendResponse({ success: true, data: emailContent });
        } catch (error) {
            console.error('Error extracting email content:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    // Return true to indicate we will send a response asynchronously
    return true;
});

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Content script received message:', request);
    
    if (request.type === 'UPDATE_EMAIL_VIEW') {
        try {
            const emailContent = extractEmailContent();
            analyzeEmail(emailContent);
        } catch (error) {
            console.error('Error processing email view update:', error);
        }
    }
    
    return true; // Keep the message channel open for async response
});

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getEmailContent") {
        try {
            const emailData = extractEmailContent();
            sendResponse({ success: true, data: emailData });
        } catch (error) {
            sendResponse({ success: false, error: error.message });
        }
    }
    return true; // Required for async response
});

// Observe DOM changes to detect when email view changes
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // Check if the added nodes contain an email view
            const emailView = mutation.target.querySelector('div[role="main"]');
            if (emailView) {
                // Notify the extension that a new email is being viewed
                chrome.runtime.sendMessage({
                    type: 'EMAIL_VIEW_CHANGED',
                    data: extractEmailContent()
                });
            }
        }
    }
});

// Start observing the Gmail interface
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Add Lovable styles to Gmail
const style = document.createElement('style');
style.textContent = `
    .cognitive-email-analysis {
        margin: 16px 0;
    }
    
    .lovable-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    .lovable-header {
        padding: 16px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .lovable-title {
        margin: 0;
        font-size: 18px;
        color: #333;
    }
    
    .lovable-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .lovable-badge.high {
        background: #ffebee;
        color: #c62828;
    }
    
    .lovable-badge.medium {
        background: #fff3e0;
        color: #ef6c00;
    }
    
    .lovable-badge.low {
        background: #e8f5e9;
        color: #2e7d32;
    }
    
    .lovable-content {
        padding: 16px;
    }
    
    .lovable-section {
        margin-bottom: 16px;
    }
    
    .lovable-subtitle {
        margin: 0 0 8px;
        font-size: 14px;
        color: #666;
    }
    
    .lovable-text {
        margin: 0;
        font-size: 16px;
        color: #333;
    }
    
    .lovable-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .lovable-tag {
        padding: 4px 8px;
        background: #f5f5f5;
        border-radius: 12px;
        font-size: 12px;
        color: #666;
    }
    
    .lovable-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .lovable-button {
        padding: 8px 16px;
        background: #1a73e8;
        border: none;
        border-radius: 8px;
        color: white;
        font-size: 14px;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .lovable-button:hover {
        background: #1557b0;
    }
    
    .lovable-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .lovable-list-item {
        padding: 8px;
        background: #f5f5f5;
        border-radius: 8px;
    }
    
    .lovable-list-title {
        display: block;
        font-size: 14px;
        color: #333;
    }
    
    .lovable-list-meta {
        display: block;
        font-size: 12px;
        color: #666;
    }
`;
document.head.appendChild(style);
console.log('Lovable styles added'); 