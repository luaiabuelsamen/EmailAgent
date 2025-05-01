document.addEventListener('DOMContentLoaded', function() {
    console.log('Popup loaded');
    const authButton = document.getElementById('auth-button');
    const statusDiv = document.getElementById('status');
    const emailAnalysis = document.getElementById('email-analysis');

    // For testing, we'll show the analysis section
    emailAnalysis.classList.remove('hidden');
    
    // Update with test data
    document.getElementById('primary-intent').textContent = 'Test Intent';
    document.getElementById('priority-level').textContent = 'High';
    
    const suggestionsList = document.getElementById('suggestions-list');
    suggestionsList.innerHTML = '';
    ['Test suggestion 1', 'Test suggestion 2'].forEach(suggestion => {
        const li = document.createElement('li');
        li.textContent = suggestion;
        suggestionsList.appendChild(li);
    });

    // Update status
    statusDiv.innerHTML = '<p>Extension is running in test mode</p>';

    // Check authentication status
    chrome.storage.local.get(['gmail_token'], function(result) {
        if (result.gmail_token) {
            updateAuthStatus(true);
        } else {
            updateAuthStatus(false);
        }
    });

    // Handle authentication button click
    authButton.addEventListener('click', function() {
        chrome.identity.getAuthToken({ interactive: true }, function(token) {
            if (chrome.runtime.lastError) {
                console.error(chrome.runtime.lastError);
                updateAuthStatus(false);
                return;
            }
            chrome.storage.local.set({ 'gmail_token': token }, function() {
                updateAuthStatus(true);
            });
        });
    });

    // Update UI based on authentication status
    function updateAuthStatus(isAuthenticated) {
        if (isAuthenticated) {
            authButton.textContent = 'Connected to Gmail';
            authButton.disabled = true;
            statusDiv.innerHTML = '<p>Connected to Gmail</p>';
            emailAnalysis.classList.remove('hidden');
        } else {
            authButton.textContent = 'Connect to Gmail';
            authButton.disabled = false;
            statusDiv.innerHTML = '<p>Please connect to Gmail to use the extension</p>';
            emailAnalysis.classList.add('hidden');
        }
    }

    // Listen for messages from content script
    chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
        if (request.type === 'EMAIL_ANALYSIS') {
            updateEmailAnalysis(request.analysis);
        }
    });

    // Update email analysis in popup
    function updateEmailAnalysis(analysis) {
        document.getElementById('primary-intent').textContent = analysis.primaryIntent;
        document.getElementById('priority-level').textContent = analysis.priority;
        
        const suggestionsList = document.getElementById('suggestions-list');
        suggestionsList.innerHTML = '';
        analysis.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
    }
}); 