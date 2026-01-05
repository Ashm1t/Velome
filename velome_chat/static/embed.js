(function () {
    // Configuration
    const CONFIG = {
        apiBase: 'http://localhost:8000',
        staticBase: 'http://localhost:8000/static'
    };

    // Load CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = `${CONFIG.staticBase}/chat.css?v=${Date.now()}`;
    document.head.appendChild(link);

    // Load Marked.js
    if (!window.marked) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        document.head.appendChild(script);
    }

    // HTML Structure
    const html = `
    <div class="velome-chat-widget">
        <button class="chat-toggle-btn">
            <span class="chat-toggle-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white" />
                </svg>
            </span>
        </button>

        <div class="chat-window">
            <div class="chat-header">
                <div class="header-info">
                    <div class="avatar-container">
                        <img src="${CONFIG.staticBase}/velome-logo.png" alt="Velo" class="bot-avatar">
                        <span class="status-dot"></span>
                    </div>
                    <div class="chat-title-group">
                        <span class="chat-title">Velo</span>
                        <span class="chat-subtitle">Velome AI Assistant</span>
                    </div>
                </div>
                <button class="close-btn">&times;</button>
            </div>

            <div class="chat-messages">
                <div class="message bot">
                    Hi there! 👋 I'm <b>Velo</b>, your travel companion. I can help you with eSIM plans, pricing, and installation.
                    <br><br>
                    <b>How may I assist you today?</b>
                </div>
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>

            <div class="chat-input-area">
                <input type="text" class="chat-input" placeholder="Type your message...">
                <button class="send-btn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    `;

    // Inject HTML
    const container = document.createElement('div');
    container.innerHTML = html;
    document.body.appendChild(container);

    // Chat Logic
    function initChat() {
        const chatWidget = document.querySelector('.velome-chat-widget');
        if (!chatWidget) return setTimeout(initChat, 500); // Retry if not in DOM

        const toggleBtn = chatWidget.querySelector('.chat-toggle-btn');
        const chatWindow = chatWidget.querySelector('.chat-window');
        const closeBtn = chatWidget.querySelector('.close-btn');
        const input = chatWidget.querySelector('.chat-input');
        const sendBtn = chatWidget.querySelector('.send-btn');
        const messagesContainer = chatWidget.querySelector('.chat-messages');
        const typingIndicator = chatWidget.querySelector('.typing-indicator');

        let isOpen = false;

        // Session ID
        let sessionId = localStorage.getItem('velo_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('velo_session_id', sessionId);
        }

        function toggleChat() {
            isOpen = !isOpen;
            if (isOpen) {
                chatWindow.classList.add('open');
                input.focus();
            } else {
                chatWindow.classList.remove('open');
            }
        }

        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showTyping() {
            typingIndicator.style.display = 'flex';
            messagesContainer.appendChild(typingIndicator);
            scrollToBottom();
        }

        function hideTyping() {
            typingIndicator.style.display = 'none';
        }

        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.classList.add('message', sender);

            if (sender === 'bot') {
                if (window.marked) {
                    div.innerHTML = marked.parse(text);
                } else {
                    div.innerHTML = text; // Fallback
                }
            } else {
                div.textContent = text;
            }

            if (typingIndicator && typingIndicator.parentNode === messagesContainer) {
                messagesContainer.insertBefore(div, typingIndicator);
            } else {
                messagesContainer.appendChild(div);
            }
            scrollToBottom();
        }

        async function sendMessage() {
            const text = input.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            input.value = '';
            input.disabled = true;
            sendBtn.disabled = true;
            showTyping();

            try {
                const response = await fetch(`${CONFIG.apiBase}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, session_id: sessionId })
                });

                const data = await response.json();
                if (response.ok) {
                    addMessage(data.response, 'bot');
                } else {
                    addMessage("Error: " + (data.detail || "Unknown error"), 'bot');
                }
            } catch (error) {
                console.error(error);
                addMessage("Error connecting to server.", 'bot');
            } finally {
                hideTyping();
                input.disabled = false;
                sendBtn.disabled = false;
                input.focus();
            }
        }

        toggleBtn.addEventListener('click', toggleChat);
        closeBtn.addEventListener('click', toggleChat);
        sendBtn.addEventListener('click', sendMessage);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChat);
    } else {
        initChat();
    }
})();
