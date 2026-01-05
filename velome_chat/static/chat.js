document.addEventListener('DOMContentLoaded', () => {
    const chatWidget = document.querySelector('.velome-chat-widget');
    const toggleBtn = chatWidget.querySelector('.chat-toggle-btn');
    const chatWindow = chatWidget.querySelector('.chat-window');
    const closeBtn = chatWidget.querySelector('.close-btn');
    const input = chatWidget.querySelector('.chat-input');
    const sendBtn = chatWidget.querySelector('.send-btn');
    const messagesContainer = chatWidget.querySelector('.chat-messages');
    const typingIndicator = chatWidget.querySelector('.typing-indicator');

    let isOpen = false;

    // Backend URL - Relative path works best when hosted on same server
    const API_URL = '/chat';

    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.classList.add('open');
            input.focus();
        } else {
            chatWindow.classList.remove('open');
        }
    }

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('message', sender);

        if (sender === 'bot') {
            // Parse markdown for bot messages
            div.innerHTML = marked.parse(text);
        } else {
            // Keep user messages as plain text for security
            div.textContent = text;
        }

        // Insert before typing indicator
        if (typingIndicator && typingIndicator.parentNode === messagesContainer) {
            messagesContainer.insertBefore(div, typingIndicator);
        } else {
            messagesContainer.appendChild(div);
        }

        scrollToBottom();
    }

    function showTyping() {
        typingIndicator.style.display = 'flex';
        messagesContainer.appendChild(typingIndicator); // Ensure it's at bottom
        scrollToBottom();
    }

    function hideTyping() {
        typingIndicator.style.display = 'none';
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Generate or retrieve Session ID
    let sessionId = localStorage.getItem('velo_session_id');
    if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('velo_session_id', sessionId);
    }

    async function sendMessage() {
        const text = input.value.trim();
        console.log("Sending: ", text);
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;

        showTyping();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId
                })
            });

            const data = await response.json();

            if (response.ok) {
                addMessage(data.response, 'bot');
            } else {
                addMessage("Sorry, something went wrong. " + (data.detail || ""), 'bot');
            }

        } catch (error) {
            console.error(error);
            addMessage("Error connecting to server. Is the backend running?", 'bot');
        } finally {
            hideTyping();
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    // Event Listeners
    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    sendBtn.addEventListener('click', sendMessage);

    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
