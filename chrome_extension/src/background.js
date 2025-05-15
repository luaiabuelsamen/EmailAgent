// Initialize the service worker
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

// Handle Gmail API authentication
chrome.identity.getAuthToken({ interactive: true }, function(token) {
  if (chrome.runtime.lastError) {
    console.error('Auth Error:', chrome.runtime.lastError);
    return;
  }
  // Store the token for later use
  chrome.storage.local.set({ 'gmail_token': token });
});

// Keep track of popup window
let popupWindow = null;

// Listen for popup window creation
chrome.windows.onCreated.addListener((window) => {
    if (window.type === 'popup') {
        popupWindow = window;
    }
});

// Listen for popup window removal
chrome.windows.onRemoved.addListener((windowId) => {
    if (popupWindow && popupWindow.id === windowId) {
        popupWindow = null;
    }
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Received message:', request.type);
    
    if (request.type === 'GET_EMAILS') {
        getEmails()
            .then(response => {
                console.log('Emails fetched:', response);
                sendResponse({
                    success: true,
                    messages: response.messages || []
                });
            })
            .catch(error => {
                console.error('Error getting emails:', error);
                sendResponse({
                    success: false,
                    error: error.message || 'Failed to fetch emails'
                });
            });
        return true;
    }
    
    if (request.type === 'ANALYZE_EMAIL') {
        analyzeEmail(request.emailId)
            .then(analysis => {
                console.log('Email analyzed:', analysis);
                sendResponse({
                    type: 'ANALYZE_EMAIL',
                    ...analysis
                });
            })
            .catch(error => {
                console.error('Error analyzing email:', error);
                sendResponse({
                    type: 'ANALYZE_EMAIL',
                    error: error.message || 'Failed to analyze email'
                });
            });
        return true;
    }
});

async function getEmails() {
  try {
    const { gmail_token } = await chrome.storage.local.get('gmail_token');
    if (!gmail_token) {
      throw new Error('No Gmail token found');
    }

    // Calculate date for 24 hours ago
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    const afterDate = oneDayAgo.toISOString().split('T')[0]; // Format: YYYY-MM-DD

    // Get emails from the last 24 hours
    const response = await fetch(
      `https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=10&q=after:${afterDate}`,
      {
        headers: {
          'Authorization': `Bearer ${gmail_token}`
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Gmail API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Get full details for each email
    const emailDetails = await Promise.all(
      data.messages.map(async (message) => {
        const emailContent = await getEmailContent(message.id);
        return {
          id: message.id,
          ...emailContent
        };
      })
    );

    return {
      messages: emailDetails
    };
  } catch (error) {
    console.error('Error in getEmails:', error);
    throw error;
  }
}

async function getEmailContent(emailId) {
  try {
    const { gmail_token } = await chrome.storage.local.get('gmail_token');
    if (!gmail_token) {
      throw new Error('No Gmail token found');
    }

    const response = await fetch(`https://www.googleapis.com/gmail/v1/users/me/messages/${emailId}`, {
      headers: {
        'Authorization': `Bearer ${gmail_token}`
      }
    });

    if (!response.ok) {
      throw new Error(`Gmail API error: ${response.status}`);
    }

    const data = await response.json();
    return decodeEmailContent(data);
  } catch (error) {
    console.error('Error in getEmailContent:', error);
    throw error;
  }
}

function decodeEmailContent(emailData) {
  try {
    let content = '';
    let subject = '';
    let from = '';
    let to = '';
    let date = '';

    // Get headers
    if (emailData.payload && emailData.payload.headers) {
      subject = getHeader(emailData.payload.headers, 'Subject');
      from = getHeader(emailData.payload.headers, 'From');
      to = getHeader(emailData.payload.headers, 'To');
      date = getHeader(emailData.payload.headers, 'Date');
    }

    // Get content
    if (emailData.payload) {
      content = extractContent(emailData.payload);
    }

    // Clean up the content
    content = content
      .replace(/<[^>]*>/g, ' ') // Remove HTML tags
      .replace(/\r\n/g, ' ') // Replace newlines with spaces
      .replace(/\n/g, ' ')
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/&nbsp;/g, ' ') // Replace HTML non-breaking spaces
      .replace(/&amp;/g, '&') // Replace HTML entities
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&mdash;/g, '—')
      .replace(/&ndash;/g, '–')
      .replace(/&hellip;/g, '...')
      .replace(/&ldquo;/g, '"')
      .replace(/&rdquo;/g, '"')
      .replace(/&lsquo;/g, "'")
      .replace(/&rsquo;/g, "'")
      .replace(/[\u200B-\u200D\uFEFF]/g, '') // Remove zero-width spaces
      .trim();

    return {
      subject,
      from,
      to,
      date,
      content
    };
  } catch (error) {
    console.error('Error decoding email content:', error);
    throw error;
  }
}

function extractContent(payload) {
  let content = '';

  // Handle multipart messages
  if (payload.parts) {
    // First try to find plain text
    const plainTextPart = payload.parts.find(part => part.mimeType === 'text/plain');
    if (plainTextPart && plainTextPart.body && plainTextPart.body.data) {
      content = decodeBase64(plainTextPart.body.data);
    } else {
      // If no plain text, try HTML
      const htmlPart = payload.parts.find(part => part.mimeType === 'text/html');
      if (htmlPart && htmlPart.body && htmlPart.body.data) {
        content = decodeBase64(htmlPart.body.data);
      }
    }

    // If still no content, recursively check nested parts
    if (!content) {
      for (const part of payload.parts) {
        if (part.parts) {
          content = extractContent(part);
          if (content) break;
        }
      }
    }
  } else if (payload.body) {
    // Handle single part messages
    if (payload.body.data) {
      content = decodeBase64(payload.body.data);
    } else if (payload.body.attachmentId) {
      // Handle attachments if needed
      console.log('Email contains attachment:', payload.body.attachmentId);
    }
  }

  return content;
}

function decodeBase64(encoded) {
  try {
    const decoded = atob(encoded.replace(/-/g, '+').replace(/_/g, '/'));
    // Handle UTF-8 encoding
    return decodeURIComponent(escape(decoded));
  } catch (error) {
    console.error('Error decoding base64:', error);
    return '';
  }
}

function getHeader(headers, name) {
  const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
  return header ? header.value : '';
}

function parseGmailDate(dateStr) {
  try {
    // Parse Gmail date format (e.g., "Thu, 15 May 2025 06:12:39 +0000")
    const date = new Date(dateStr);
    // Format as ISO string with timezone offset
    const tzOffset = date.getTimezoneOffset() * 60000; // Convert to milliseconds
    const localISOTime = (new Date(date.getTime() - tzOffset)).toISOString();
    return localISOTime;
  } catch (error) {
    console.error('Error parsing date:', error);
    return new Date().toISOString(); // Fallback to current time
  }
}

// Cache for email analysis results
const analysisCache = new Map();

async function analyzeEmail(emailId) {
    try {
        // Check cache first
        if (analysisCache.has(emailId)) {
            console.log('Using cached analysis for:', emailId);
            return analysisCache.get(emailId);
        }

        console.log('Starting email analysis for:', emailId);
        const emailContent = await getEmailContent(emailId);
        console.log('FFF Email content fetched:', emailContent);

        // Get recent emails for context
        const recentEmails = await getRecentEmails(emailId);
        console.log('Recent emails fetched:', recentEmails.length);

        // Prepare the request payload
        const requestData = {
            current_email: {
                sender: emailContent.from,
                recipients: [emailContent.to],
                subject: emailContent.subject,
                body: emailContent.content,
                timestamp: parseGmailDate(emailContent.date),
                thread_id: emailId
            },
            recent_emails: recentEmails.map(email => ({
                ...email,
                timestamp: parseGmailDate(email.timestamp)
            }))
        };

        console.log('Sending request to backend:', requestData);
        const response = await fetch('http://localhost:8000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const analysis = await response.json();
        console.log('Analysis received:', analysis);
        
        // Cache the analysis result
        analysisCache.set(emailId, analysis);
        
        return analysis;
    } catch (error) {
        console.error('Error analyzing email:', error);
        throw error;
    }
}

async function getRecentEmails(currentEmailId) {
  try {
    const { gmail_token } = await chrome.storage.local.get('gmail_token');
    if (!gmail_token) {
      throw new Error('No Gmail token found');
    }

    // Get 10 most recent emails for better context
    const response = await fetch(
      'https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=10',
      {
        headers: {
          'Authorization': `Bearer ${gmail_token}`
        }
      }
    );

    if (!response.ok) {
      throw new Error(`Gmail API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Get full details for each email, excluding the current one
    const recentEmails = await Promise.all(
      data.messages
        .filter(message => message.id !== currentEmailId)
        .map(async (message) => {
          const emailContent = await getEmailContent(message.id);
          return {
            subject: emailContent.subject,
            sender: emailContent.from,
            recipients: [emailContent.to],
            body: emailContent.content,
            snippet: emailContent.content.substring(0, 100),
            timestamp: parseGmailDate(emailContent.date), // Use parseGmailDate for consistent formatting
            thread_id: message.id
          };
        })
    );

    console.log('Recent emails fetched:', recentEmails.length);
    return recentEmails;
  } catch (error) {
    console.error('Error getting recent emails:', error);
    return [];
  }
} 