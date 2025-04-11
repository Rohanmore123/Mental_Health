// Chat Interface JavaScript

// Global variables
let currentChatType = 'ai'; // 'ai' or 'doctor'
let currentContactId = null;
let chatContacts = [];
let lastMessageTimestamp = null;

// Initialize chat interface
function initializeChatInterface() {
    console.log('Initializing chat interface...');

    // Set up event listeners
    document.getElementById('ai-chat-btn').addEventListener('click', () => switchChatType('ai'));
    document.getElementById('doctor-chat-btn').addEventListener('click', () => switchChatType('doctor'));

    // Set up chat form
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }

    // Set up voice input
    const voiceInputBtn = document.getElementById('voice-input-btn');
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener('click', startVoiceInput);
    }

    // Initialize with AI chat
    switchChatType('ai');

    // Set up contact search
    const contactSearch = document.getElementById('contact-search');
    if (contactSearch) {
        contactSearch.addEventListener('input', filterContacts);
    }

    // Set up polling for new messages
    setInterval(checkForNewMessages, 10000); // Check every 10 seconds
}

// Switch between AI and doctor chat
function switchChatType(type) {
    console.log(`Switching chat type to: ${type}`);
    currentChatType = type;

    // Update UI
    const aiChatBtn = document.getElementById('ai-chat-btn');
    const doctorChatBtn = document.getElementById('doctor-chat-btn');
    const chatContacts = document.getElementById('chat-contacts');
    const chatAvatar = document.getElementById('chat-avatar');
    const chatRecipientName = document.getElementById('chat-recipient-name');
    const chatRecipientStatus = document.getElementById('chat-recipient-status');

    if (type === 'ai') {
        aiChatBtn.classList.add('active');
        doctorChatBtn.classList.remove('active');
        chatContacts.style.display = 'none';

        // Set AI chat header
        chatAvatar.src = '/static/img/ai-avatar.svg';
        chatRecipientName.textContent = 'AI Health Assistant';
        chatRecipientStatus.textContent = 'Always available';

        // Load AI chat messages
        loadAIChatMessages();
    } else {
        aiChatBtn.classList.remove('active');
        doctorChatBtn.classList.add('active');
        chatContacts.style.display = 'flex';

        // Load contacts
        loadChatContacts();

        // Show empty state if no contact is selected
        if (!currentContactId) {
            showEmptyContactState();
        }
    }
}

// Load chat contacts
async function loadChatContacts() {
    console.log('Loading chat contacts...');
    const contactsList = document.getElementById('chat-contacts-list');

    try {
        // Show loading state
        contactsList.innerHTML = `
            <div class="text-center p-3 text-muted">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading contacts...</p>
            </div>
        `;

        // Fetch contacts from API
        const response = await apiCall('/chat/contacts');
        chatContacts = response || [];

        // Render contacts
        renderChatContacts();

        // Select first contact if available and none is selected
        if (chatContacts.length > 0 && !currentContactId) {
            selectContact(chatContacts[0].user_id);
        }
    } catch (error) {
        console.error('Error loading chat contacts:', error);
        contactsList.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-circle mb-2"></i>
                <p>Failed to load contacts. Please try again.</p>
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadChatContacts()">
                    <i class="fas fa-sync-alt me-1"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render chat contacts
function renderChatContacts() {
    const contactsList = document.getElementById('chat-contacts-list');

    if (chatContacts.length === 0) {
        contactsList.innerHTML = `
            <div class="text-center p-3 text-muted">
                <i class="fas fa-user-slash mb-2" style="font-size: 2rem;"></i>
                <p>No contacts available</p>
            </div>
        `;
        return;
    }

    let html = '';

    chatContacts.forEach(contact => {
        const isActive = currentContactId === contact.user_id;
        const hasUnread = contact.unread_count > 0;

        html += `
            <div class="chat-contact ${isActive ? 'active' : ''}" data-contact-id="${contact.user_id}" onclick="selectContact('${contact.user_id}')">
                <img src="${contact.profile_image || '/static/img/default-avatar.svg'}" alt="${contact.name}" class="chat-contact-avatar">
                <div class="chat-contact-info">
                    <div class="chat-contact-name">${contact.name}</div>
                    <div class="chat-contact-last-message">${contact.last_message || 'No messages yet'}</div>
                </div>
                <div class="chat-contact-meta">
                    ${contact.last_message_time ? `<div class="chat-contact-time">${formatChatTime(new Date(contact.last_message_time))}</div>` : ''}
                    ${hasUnread ? `<div class="chat-contact-badge">${contact.unread_count}</div>` : ''}
                </div>
            </div>
        `;
    });

    contactsList.innerHTML = html;
}

// Select a contact
function selectContact(contactId) {
    console.log(`Selecting contact: ${contactId}`);
    currentContactId = contactId;

    // Update UI
    const contacts = document.querySelectorAll('.chat-contact');
    contacts.forEach(contact => {
        if (contact.dataset.contactId === contactId) {
            contact.classList.add('active');
        } else {
            contact.classList.remove('active');
        }
    });

    // Find the selected contact
    const selectedContact = chatContacts.find(c => c.user_id === contactId);
    if (selectedContact) {
        // Update chat header
        const chatAvatar = document.getElementById('chat-avatar');
        const chatRecipientName = document.getElementById('chat-recipient-name');
        const chatRecipientStatus = document.getElementById('chat-recipient-status');

        chatAvatar.src = selectedContact.profile_image || '/static/img/default-avatar.svg';
        chatRecipientName.textContent = selectedContact.name;
        chatRecipientStatus.textContent = `${selectedContact.role.charAt(0).toUpperCase() + selectedContact.role.slice(1)}`;

        // Load messages for this contact
        loadContactMessages(contactId);
    }
}

// Load AI chat messages
async function loadAIChatMessages() {
    console.log('Loading AI chat messages...');
    const chatMessages = document.getElementById('chat-messages');

    try {
        // Show loading state
        chatMessages.innerHTML = `
            <div class="text-center p-3 text-muted">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading messages...</p>
            </div>
        `;

        // Fetch messages from API
        const response = await apiCall('/chat/messages');
        console.log('AI chat messages response:', response);

        // Filter messages for AI chat (where sender_id is null or receiver_id is null)
        const messages = response.messages ? response.messages.filter(msg =>
            msg.sender_id === null || msg.receiver_id === null
        ) : [];

        console.log('Filtered AI messages:', messages);

        // Render messages
        renderChatMessages(messages, 'ai');

        // If no messages, show welcome message
        if (messages.length === 0) {
            chatMessages.innerHTML = `
                <div class="chat-start-message">
                    <img src="/static/img/ai-avatar.svg" alt="AI" class="chat-start-avatar">
                    <h5>AI Health Assistant</h5>
                    <p>Ask me any health-related questions, and I'll do my best to help you.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading AI chat messages:', error);
        chatMessages.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-circle mb-2"></i>
                <p>Failed to load messages. Please try again.</p>
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadAIChatMessages()">
                    <i class="fas fa-sync-alt me-1"></i> Retry
                </button>
            </div>
        `;
    }
}

// Load messages for a specific contact
async function loadContactMessages(contactId) {
    console.log(`Loading messages for contact: ${contactId}`);
    const chatMessages = document.getElementById('chat-messages');

    try {
        // Show loading state
        chatMessages.innerHTML = `
            <div class="text-center p-3 text-muted">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading messages...</p>
            </div>
        `;

        // Fetch messages from API
        const response = await apiCall('/chat/messages');
        console.log('Contact messages response:', response);

        // Filter messages for this contact
        const messages = response.messages ? response.messages.filter(msg =>
            (msg.sender_id === contactId && msg.receiver_id === getUserId()) ||
            (msg.sender_id === getUserId() && msg.receiver_id === contactId)
        ) : [];

        console.log(`Filtered messages for contact ${contactId}:`, messages);

        // Render messages
        renderChatMessages(messages, 'doctor');

        // If no messages, show empty state
        if (messages.length === 0) {
            const selectedContact = chatContacts.find(c => c.user_id === contactId);
            chatMessages.innerHTML = `
                <div class="chat-start-message">
                    <img src="${selectedContact?.profile_image || '/static/img/default-avatar.svg'}" alt="${selectedContact?.name}" class="chat-start-avatar">
                    <h5>${selectedContact?.name}</h5>
                    <p>Start a conversation with ${selectedContact?.name}.</p>
                </div>
            `;
        }

        // Update last message timestamp
        if (messages.length > 0) {
            lastMessageTimestamp = new Date(messages[messages.length - 1].timestamp);
        }
    } catch (error) {
        console.error(`Error loading messages for contact ${contactId}:`, error);
        chatMessages.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="fas fa-exclamation-circle mb-2"></i>
                <p>Failed to load messages. Please try again.</p>
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadContactMessages('${contactId}')">
                    <i class="fas fa-sync-alt me-1"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render chat messages
function renderChatMessages(messages, chatType) {
    const chatMessages = document.getElementById('chat-messages');
    let html = '';

    messages.forEach(message => {
        const isUserMessage = message.sender_id === getUserId();
        const messageClass = isUserMessage ? 'user-message' : (chatType === 'ai' ? 'ai-message' : 'doctor-message');
        const messageTime = formatChatTime(new Date(message.timestamp));

        html += `
            <div class="message ${messageClass}">
                <div class="message-content">
                    <p>${message.message_text}</p>
                    <div class="message-time">${messageTime}</div>
                </div>
            </div>
        `;
    });

    chatMessages.innerHTML = html;

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle chat form submission
async function handleChatSubmit(event) {
    event.preventDefault();

    const chatInput = document.getElementById('chat-message');
    const message = chatInput.value.trim();

    if (!message) return;

    // Clear input
    chatInput.value = '';

    // Add message to UI immediately
    addMessageToChat('user', message);

    try {
        if (currentChatType === 'ai') {
            // Send message to AI
            await sendMessageToAI(message);
        } else if (currentChatType === 'doctor' && currentContactId) {
            // Send message to doctor
            await sendMessageToContact(message, currentContactId);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showError('Failed to send message. Please try again.');
    }
}

// Send message to AI
async function sendMessageToAI(message) {
    console.log('Sending message to AI:', message);

    try {
        // Create message in database
        await apiCall('/chat/messages', 'POST', {
            message_text: message,
            receiver_id: null // null receiver_id indicates AI chat
        });

        // Get AI response
        const aiResponse = await apiCall('/ai-chat/text', 'POST', { message });

        if (aiResponse && aiResponse.response) {
            // Add AI response to chat
            addMessageToChat('ai', aiResponse.response);

            // Create AI response in database
            await apiCall('/chat/messages', 'POST', {
                message_text: aiResponse.response,
                sender_id: null, // null sender_id indicates AI message
                receiver_id: getUserId()
            });
        } else {
            throw new Error('Invalid AI response');
        }
    } catch (error) {
        console.error('Error in AI chat:', error);
        addMessageToChat('ai', 'Sorry, I encountered an error processing your request.');
    }
}

// Send message to contact
async function sendMessageToContact(message, contactId) {
    console.log(`Sending message to contact ${contactId}:`, message);

    try {
        // Create message in database
        await apiCall('/chat/messages', 'POST', {
            message_text: message,
            receiver_id: contactId
        });

        // Update contact's last message
        const contactIndex = chatContacts.findIndex(c => c.user_id === contactId);
        if (contactIndex !== -1) {
            chatContacts[contactIndex].last_message = message;
            chatContacts[contactIndex].last_message_time = new Date().toISOString();

            // Re-render contacts to update UI
            renderChatContacts();
        }
    } catch (error) {
        console.error(`Error sending message to contact ${contactId}:`, error);
        showError('Failed to send message. Please try again.');
    }
}

// Add message to chat UI
function addMessageToChat(type, text) {
    const chatMessages = document.getElementById('chat-messages');
    const messageClass = type === 'user' ? 'user-message' : (type === 'ai' ? 'ai-message' : 'doctor-message');
    const messageTime = formatChatTime(new Date());

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${messageClass}`;

    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${text}</p>
            <div class="message-time">${messageTime}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Check for new messages
async function checkForNewMessages() {
    if (!isLoggedIn()) return;

    try {
        if (currentChatType === 'doctor' && currentContactId) {
            // Check for new messages from current contact
            const response = await apiCall(`/chat/messages?receiver_id=${currentContactId}`);
            const messages = response.messages || [];

            if (messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                const lastMessageTime = new Date(lastMessage.timestamp);

                if (!lastMessageTimestamp || lastMessageTime > lastMessageTimestamp) {
                    // New messages found, reload conversation
                    loadContactMessages(currentContactId);
                }
            }
        }

        // Refresh contacts list to update unread counts
        if (currentChatType === 'doctor') {
            loadChatContacts();
        }
    } catch (error) {
        console.error('Error checking for new messages:', error);
    }
}

// Filter contacts by search term
function filterContacts() {
    const searchTerm = document.getElementById('contact-search').value.toLowerCase();

    if (!searchTerm) {
        // If search is empty, show all contacts
        renderChatContacts();
        return;
    }

    // Filter contacts by name
    const filteredContacts = chatContacts.filter(contact =>
        contact.name.toLowerCase().includes(searchTerm)
    );

    // Store original contacts
    const originalContacts = chatContacts;

    // Set filtered contacts and render
    chatContacts = filteredContacts;
    renderChatContacts();

    // Restore original contacts
    chatContacts = originalContacts;
}

// Show empty contact state
function showEmptyContactState() {
    const chatMessages = document.getElementById('chat-messages');
    const chatRecipientName = document.getElementById('chat-recipient-name');
    const chatRecipientStatus = document.getElementById('chat-recipient-status');
    const chatAvatar = document.getElementById('chat-avatar');

    chatRecipientName.textContent = 'Select a Contact';
    chatRecipientStatus.textContent = '';
    chatAvatar.src = '/static/img/default-avatar.svg';

    chatMessages.innerHTML = `
        <div class="chat-empty-state">
            <i class="fas fa-comments chat-empty-icon"></i>
            <h5>No conversation selected</h5>
            <p>Select a contact to start chatting</p>
        </div>
    `;
}

// Start voice input
function startVoiceInput() {
    if (!('webkitSpeechRecognition' in window)) {
        showError('Voice input is not supported in your browser.');
        return;
    }

    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        const voiceBtn = document.getElementById('voice-input-btn');
        voiceBtn.classList.add('btn-danger');
        voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        showSuccess('Listening...');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('chat-message').value = transcript;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        showError(`Voice input error: ${event.error}`);
    };

    recognition.onend = () => {
        const voiceBtn = document.getElementById('voice-input-btn');
        voiceBtn.classList.remove('btn-danger');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };

    recognition.start();
}

// Format chat time
function formatChatTime(date) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const isToday = date >= today;
    const isYesterday = date >= yesterday && date < today;

    if (isToday) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (isYesterday) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
}

// Get user ID from localStorage
function getUserId() {
    return localStorage.getItem('userId');
}

// Initialize chat when document is ready
document.addEventListener('DOMContentLoaded', function() {
    if (isLoggedIn()) {
        initializeChatInterface();
    }
});
