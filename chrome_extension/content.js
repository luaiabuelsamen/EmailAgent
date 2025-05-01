// Function to get the current email ID from Gmail's URL
function getCurrentEmailId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('message_id') || urlParams.get('id');
}

// Function to extract email content from Gmail's DOM
function extractEmailContent() {
    console.log('Attempting to extract email content...');
    const emailContent = document.querySelector('.a3s.aiL');
    if (!emailContent) {
        console.log('No email content found');
        return null;
    }

    const content = {
        subject: document.querySelector('h2.hP')?.textContent || 'No Subject',
        from: document.querySelector('.gD')?.textContent || 'Unknown Sender',
        body: emailContent.textContent,
        timestamp: document.querySelector('.g3')?.textContent || ''
    };
    
    console.log('Extracted email content:', content);
    return content;
}

// Function to analyze email content
function analyzeEmail(email) {
    console.log('Analyzing email:', email);
    // For testing, we'll just show some mock analysis
    const mockAnalysis = {
        primaryIntent: 'Test Intent',
        priority: 'High',
        suggestions: ['Test suggestion 1', 'Test suggestion 2']
    };
    
    updateUI(mockAnalysis);
}

// Function to update the UI with analysis results
function updateUI(analysis) {
    console.log('Updating UI with analysis:', analysis);
    const analysisContainer = document.createElement('div');
    analysisContainer.className = 'cognitive-email-analysis';
    analysisContainer.innerHTML = `
        <div class="analysis-header">
            <h3>Cognitive Analysis</h3>
        </div>
        <div class="analysis-content">
            <div class="intent">
                <strong>Primary Intent:</strong> ${analysis.primaryIntent}
            </div>
            <div class="priority">
                <strong>Priority Level:</strong> ${analysis.priority}
            </div>
            <div class="suggestions">
                <strong>Suggested Actions:</strong>
                <ul>
                    ${analysis.suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
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
    if (currentEmailId && currentEmailId !== lastEmailId) {
        console.log('New email detected:', currentEmailId);
        lastEmailId = currentEmailId;
        const emailContent = extractEmailContent();
        if (emailContent) {
            analyzeEmail(emailContent);
        }
    }
}, 1000);

// Add custom styles to Gmail
const style = document.createElement('style');
style.textContent = `
    .cognitive-email-analysis {
        background-color: #f8f9fa;
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    .analysis-header h3 {
        color: #1a73e8;
        margin: 0 0 12px 0;
    }
    .analysis-content {
        color: #202124;
    }
    .analysis-content div {
        margin-bottom: 8px;
    }
    .analysis-content ul {
        margin: 8px 0;
        padding-left: 20px;
    }
    .analysis-content li {
        margin-bottom: 4px;
    }
`;
document.head.appendChild(style);
console.log('Extension styles added'); 