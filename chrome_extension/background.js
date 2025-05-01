// Configuration for Gmail API OAuth2
const CLIENT_ID = '579362248829-g2sevv19cfinv8rmnd9qnapl82g42ul8.apps.googleusercontent.com';
const SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'];

// Backend API URL
const BACKEND_API_URL = 'http://localhost:8000';

// Handle installation and updates
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        console.log('Extension installed');
    } else if (details.reason === 'update') {
        console.log('Extension updated');
    }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Received message:', message);
    
    if (message.type === 'PING') {
        // Respond to ping to confirm connection
        sendResponse({ connected: true });
        return true;
    }
    
    if (message.type === 'EMAIL_VIEW_CHANGED') {
        try {
            // Get the current active tab
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (tabs[0]) {
                    // Send message only to the active tab
                    chrome.tabs.sendMessage(tabs[0].id, {
                        type: 'UPDATE_EMAIL_VIEW',
                        data: message.data
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Error sending message to tab:', chrome.runtime.lastError);
                        }
                    });
                }
            });
        } catch (error) {
            console.error('Error handling EMAIL_VIEW_CHANGED:', error);
        }
    } else if (message.type === 'GET_EMAIL') {
        // Get the email content from Gmail API
        getEmailContent(message.emailId)
            .then(email => {
                // Send email to backend for analysis
                return analyzeEmail(email);
            })
            .then(analysis => {
                sendResponse({ success: true, analysis });
            })
            .catch(error => {
                console.error('Error processing email:', error);
                sendResponse({ success: false, error: error.message });
            });
        return true; // Keep the message channel open for async response
    }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    // Only activate on Gmail tabs
    if (tab.url && tab.url.includes('mail.google.com')) {
        chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE_ANALYSIS' });
    }
});

// Function to get email content from Gmail API
async function getEmailContent(emailId) {
    try {
        const response = await fetch(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${emailId}`, {
            headers: {
                'Authorization': `Bearer ${await getAuthToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Gmail API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Extract email content
        const email = {
            emailId: data.id,
            subject: getHeader(data.payload.headers, 'Subject'),
            from: getHeader(data.payload.headers, 'From'),
            to: getHeader(data.payload.headers, 'To').split(',').map(e => e.trim()),
            cc: getHeader(data.payload.headers, 'Cc')?.split(',').map(e => e.trim()) || [],
            timestamp: getHeader(data.payload.headers, 'Date'),
            body: decodeEmailBody(data.payload)
        };
        
        return email;
    } catch (error) {
        console.error('Error fetching email:', error);
        throw error;
    }
}

// Function to analyze email using backend API
async function analyzeEmail(email) {
    try {
        const response = await fetch(`${BACKEND_API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            mode: 'cors',
            credentials: 'include',
            body: JSON.stringify({
                email,
                context: {
                    // Add any additional context here
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`Backend API error: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error analyzing email:', error);
        throw error;
    }
}

// Helper function to get header value from email headers
function getHeader(headers, name) {
    const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
    return header ? header.value : '';
}

// Helper function to decode email body
function decodeEmailBody(payload) {
    if (payload.parts) {
        // Handle multipart emails
        const textPart = payload.parts.find(part => part.mimeType === 'text/plain');
        if (textPart) {
            return atob(textPart.body.data.replace(/-/g, '+').replace(/_/g, '/'));
        }
    }
    
    // Handle simple emails
    if (payload.body.data) {
        return atob(payload.body.data.replace(/-/g, '+').replace(/_/g, '/'));
    }
    
    return '';
}

// Function to get OAuth token
async function getAuthToken() {
    return new Promise((resolve, reject) => {
        chrome.identity.getAuthToken({ interactive: true }, token => {
            if (chrome.runtime.lastError) {
                reject(chrome.runtime.lastError);
            } else {
                resolve(token);
            }
        });
    });
} 