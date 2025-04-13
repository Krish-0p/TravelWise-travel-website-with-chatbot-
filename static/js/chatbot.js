/**
 * Chatbot functionality for TravelWise website
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
});

function initializeChatbot() {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotPanel = document.getElementById('chatbot-panel');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');
    
    // Toggle chatbot panel
    chatbotToggle.addEventListener('click', function() {
        chatbotPanel.style.display = 'flex';
        chatbotInput.focus();
    });
    
    // Close chatbot panel
    chatbotClose.addEventListener('click', function() {
        chatbotPanel.style.display = 'none';
    });
    
    // Send message on enter key
    chatbotInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Send message on button click
    chatbotSend.addEventListener('click', sendMessage);
    
    /**
     * Send user message to server and display response
     */
    function sendMessage() {
        const message = chatbotInput.value.trim();
        
        if (message === '') return;
        
        // Display user message
        appendMessage(message, 'user');
        
        // Clear input
        chatbotInput.value = '';
        
        // Send request to server
        fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Display bot response with a slight delay to feel more natural
            setTimeout(() => {
                appendMessage(data.response, 'bot');
                
                // Scroll to the bottom of the chat
                chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
            }, 500);
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Display error message
            setTimeout(() => {
                appendMessage("I'm sorry, I'm having trouble connecting right now. Please try again later.", 'bot');
                
                // Scroll to the bottom of the chat
                chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
            }, 500);
        });
        
        // Scroll to the bottom of the chat
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    /**
     * Append message to the chat
     */
    function appendMessage(content, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        
        if (sender === 'user') {
            messageElement.classList.add('user-message');
        } else {
            messageElement.classList.add('bot-message');
        }
        
        messageElement.textContent = content;
        chatbotMessages.appendChild(messageElement);
    }
}
