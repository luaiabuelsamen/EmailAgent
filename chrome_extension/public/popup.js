document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    let currentEmailId = null;
    let emailList = [];

    // Initialize the extension
    initializeExtension();

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button
            button.classList.add('active');

            // Show corresponding tab pane
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Update content based on the selected tab
            updateTabContent(tabId);
        });
    });

    async function initializeExtension() {
        try {
            showLoading('Loading emails...');
            
            // Get list of recent emails
            const response = await new Promise((resolve, reject) => {
                chrome.runtime.sendMessage({ type: 'GET_EMAILS' }, (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else {
                        resolve(response);
                    }
                });
            });
            
            if (!response.success) {
                throw new Error(response.error || 'Failed to fetch emails');
            }

            if (response.messages && response.messages.length > 0) {
                emailList = response.messages;
                currentEmailId = emailList[0].id;
                updateTabContent('sentiment');
                hideLoading();
            } else {
                throw new Error('No emails found');
            }
        } catch (error) {
            console.error('Error initializing extension:', error);
            showError('Failed to load emails. Please check your authentication and reload the extension.');
            hideLoading();
        }
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
                            <p class="sentiment-label">Overall Tone:</p>
                            <p class="sentiment-value ${analysis.sentiment.toLowerCase()}">${analysis.sentiment}</p>
                            <p class="confidence">Confidence: ${analysis.confidence}%</p>
                        </div>
                    `;
                    break;
                case 'summary':
                    contentBox.innerHTML = `
                        <h3>Email Summary</h3>
                        <div class="summary-content">
                            <p>${analysis.summary}</p>
                        </div>
                    `;
                    break;
                case 'suggestions':
                    contentBox.innerHTML = `
                        <h3>Writing Suggestions</h3>
                        <div class="suggestions-list">
                            <ul>
                                ${analysis.suggestions.map(suggestion => 
                                    `<li>${suggestion}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    `;
                    break;
            }
        } catch (error) {
            console.error('Error updating content:', error);
            contentBox.innerHTML = `
                <div class="error-message">
                    <p>${error.message || 'Error loading analysis. Please try again.'}</p>
                </div>
            `;
        }
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.body.insertBefore(errorDiv, document.body.firstChild);
    }

    function showLoading(message) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-overlay';
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <p>${message}</p>
        `;
        document.body.appendChild(loadingDiv);
    }

    function hideLoading() {
        const loadingDiv = document.querySelector('.loading-overlay');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
}); 