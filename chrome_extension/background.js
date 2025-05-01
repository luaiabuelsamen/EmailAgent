// Gmail API OAuth2 configuration
const CLIENT_ID = '579362248829-g2sevv19cfinv8rmnd9qnapl82g42ul8.apps.googleusercontent.com';
const SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
];

// Handle OAuth2 authentication
chrome.identity.getAuthToken({ interactive: true }, function(token) {
    if (chrome.runtime.lastError) {
        console.error('Auth error:', chrome.runtime.lastError);
        return;
    }
    console.log('Auth token received:', token);
    // Store the token for later use
    chrome.storage.local.set({ 'gmail_token': token });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GET_EMAIL') {
        getEmailContent(request.emailId)
            .then(email => sendResponse({ success: true, email }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // Required for async response
    }
});

// Function to fetch email content using Gmail API
async function getEmailContent(emailId) {
    const token = await new Promise(resolve => {
        chrome.storage.local.get(['gmail_token'], result => {
            resolve(result.gmail_token);
        });
    });

    if (!token) {
        throw new Error('No authentication token available');
    }

    const response = await fetch(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${emailId}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to fetch email');
    }

    const data = await response.json();
    return {
        subject: data.payload.headers.find(h => h.name === 'Subject')?.value || 'No Subject',
        from: data.payload.headers.find(h => h.name === 'From')?.value || 'Unknown Sender',
        body: decodeEmailBody(data.payload),
        timestamp: data.internalDate
    };
}

// Helper function to decode email body
function decodeEmailBody(payload) {
    if (payload.parts) {
        const textPart = payload.parts.find(part => part.mimeType === 'text/plain');
        if (textPart) {
            return atob(textPart.body.data.replace(/-/g, '+').replace(/_/g, '/'));
        }
    }
    return atob(payload.body.data.replace(/-/g, '+').replace(/_/g, '/'));
} 