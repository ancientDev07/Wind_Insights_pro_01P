// class AIChatUI {
//     constructor() {
//         this.chatMessages = document.getElementById('chatMessages');
//         this.messageInput = document.getElementById('messageInput');
//         this.sendBtn = document.getElementById('sendBtn');
//         this.clearBtn = document.getElementById('clearBtn');
//         this.settingsBtn = document.getElementById('settingsBtn');
//         this.settingsModal = document.getElementById('settingsModal');
//         this.statusDot = document.getElementById('statusDot');
//         this.statusText = document.getElementById('statusText');
//         this.charCount = document.getElementById('charCount');

//         this.chatHistory = [];
//         this.ollamaHost = localStorage.getItem('ollama_host') || 'http://localhost:11434';
//         this.modelName = localStorage.getItem('model_name') || 'gemma4:e2b';
        
//         this.ragEnabled = false;
//         this.chatBackend = null;  // Will be set by QWebChannel

//         this.setupEventListeners();
//         this.checkConnection();
//         this.loadSettings();
//     }

//     setupEventListeners() {
//         this.sendBtn.addEventListener('click', () => this.sendMessage());
//         this.messageInput.addEventListener('keypress', (e) => {
//             if (e.key === 'Enter' && !e.shiftKey) {
//                 e.preventDefault();
//                 this.sendMessage();
//             }
//         });
//         this.messageInput.addEventListener('input', () => this.updateCharCount());
//         this.clearBtn.addEventListener('click', () => this.clearChat());
//         this.settingsBtn.addEventListener('click', () => this.openSettings());

//         document.getElementById('closeSettings').addEventListener('click', () => this.closeSettings());
//         document.getElementById('settingsCancel').addEventListener('click', () => this.closeSettings());
//         document.getElementById('settingsSave').addEventListener('click', () => this.saveSettings());
//         document.getElementById('testConnection').addEventListener('click', () => this.testConnection());

//         this.settingsModal.addEventListener('click', (e) => {
//             if (e.target === this.settingsModal) {
//                 this.closeSettings();
//             }
//         });
    
//         const ragToggle = document.getElementById('ragToggle');
//         if (ragToggle) {
//             ragToggle.addEventListener('change', (e) => {
//                 this.ragEnabled = e.target.checked;
//                 localStorage.setItem('rag_enabled', this.ragEnabled);
//             });
//             // Load saved state
//             this.ragEnabled = localStorage.getItem('rag_enabled') === 'true';
//             ragToggle.checked = this.ragEnabled;
//         }
    
//         const indexBtn = document.getElementById('indexBtn');
//         if (indexBtn) {
//             indexBtn.addEventListener('click', () => this.indexDocuments());
//         }
//     }

//     async indexDocuments() {
//         if (!window.chatBackend) {
//             alert('Backend not available');
//             return;
//         }
    
//         const folder = prompt('Enter folder path to index:');
//         if (!folder) return;
    
//         this.statusText.textContent = 'Indexing...';
//         const success = window.chatBackend.indexDocuments(folder);
        
//         if (success) {
//             alert('✓ Documents indexed successfully');
//             this.ragEnabled = true;
//             document.getElementById('ragToggle').checked = true;
//         } else {
//             alert('✗ Indexing failed - check console');
//         }
//     }

//     updateCharCount() {
//         const count = this.messageInput.value.length;
//         this.charCount.textContent = `${count} / 8000`;

//         if (count > 8000) {
//             this.charCount.classList.add('warning');
//             this.sendBtn.disabled = true;
//         } else {
//             this.charCount.classList.remove('warning');
//             this.sendBtn.disabled = false;
//         }
//     }

//     addMessage(text, isUser) {
//         const message = document.createElement('div');
//         message.className = `message ${isUser ? 'user' : 'assistant'}`;

//         const avatar = document.createElement('div');
//         avatar.className = 'message-avatar';
//         avatar.textContent = isUser ? 'U' : 'AI';

//         const content = document.createElement('div');
//         content.className = 'message-content';

//         const bubble = document.createElement('div');
//         bubble.className = 'message-bubble';

//         if (isUser) {
//             bubble.textContent = text;
//         } else {
//             // Simple markdown conversion for AI responses
//             bubble.innerHTML = this.markdownToHtml(text);
//         }

//         const time = document.createElement('div');
//         time.className = 'message-time';
//         time.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

//         content.appendChild(bubble);
//         content.appendChild(time);

//         if (isUser) {
//             message.appendChild(content);
//             message.appendChild(avatar);
//         } else {
//             message.appendChild(avatar);
//             message.appendChild(content);
//         }

//         this.chatMessages.appendChild(message);
//         this.scrollToBottom();

//         // Remove welcome message if exists
//         const welcome = this.chatMessages.querySelector('.welcome-message');
//         if (welcome && this.chatMessages.children.length > 1) {
//             welcome.remove();
//         }

//         // Store in history
//         this.chatHistory.push({
//             role: isUser ? 'user' : 'assistant',
//             content: text,
//             timestamp: new Date()
//         });
//     }

//     markdownToHtml(text) {
//         let html = text
//             .replace(/&/g, '&amp;')
//             .replace(/</g, '&lt;')
//             .replace(/>/g, '&gt;');

//         // Code blocks
//         html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
        
//         // Inline code
//         html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

//         // Bold
//         html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

//         // Italic
//         html = html.replace(/\*([^\*]+)\*/g, '<em>$1</em>');

//         // Line breaks
//         html = html.replace(/\n/g, '<br>');

//         return html;
//     }

//     addTypingIndicator() {
//         const message = document.createElement('div');
//         message.className = 'message assistant';
//         message.id = 'typing-indicator';

//         const avatar = document.createElement('div');
//         avatar.className = 'message-avatar';
//         avatar.textContent = 'AI';

//         const content = document.createElement('div');
//         content.className = 'message-content';

//         const bubble = document.createElement('div');
//         bubble.className = 'message-bubble typing-indicator';
//         bubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

//         content.appendChild(bubble);
//         message.appendChild(avatar);
//         message.appendChild(content);

//         this.chatMessages.appendChild(message);
//         this.scrollToBottom();
//     }

//     removeTypingIndicator() {
//         const typing = document.getElementById('typing-indicator');
//         if (typing) {
//             typing.remove();
//         }
//     }

//     // async sendMessage() {
//     //     const text = this.messageInput.value.trim();

//     //     if (!text || text.length > 8000) {
//     //         return;
//     //     }

//     //     // Add user message
//     //     this.addMessage(text, true);
//     //     this.messageInput.value = '';
//     //     this.updateCharCount();

//     //     // Disable input
//     //     this.messageInput.disabled = true;
//     //     this.sendBtn.disabled = true;

//     //     // Check connection
//     //     if (!(await this.checkConnection())) {
//     //         this.showError('Cannot connect to Ollama. Make sure it is running.');
//     //         this.messageInput.disabled = false;
//     //         this.sendBtn.disabled = false;
//     //         return;
//     //     }

//     //     // Show typing indicator
//     //     this.addTypingIndicator();

//     //     // Send to backend
//     //     try {
//     //         const response = await this.callOllama(text);
//     //         this.removeTypingIndicator();
//     //         this.addMessage(response, false);
//     //     } catch (error) {
//     //         this.removeTypingIndicator();
//     //         this.showError(`Error: ${error.message}`);
//     //     }

//     //     // Re-enable input
//     //     this.messageInput.disabled = false;
//     //     this.sendBtn.disabled = false;
//     //     this.messageInput.focus();
//     // }

//     // async sendMessage() {
//     //     const text = this.messageInput.value.trim();
//     //     if (!text || text.length > 8000) return;

//     //     this.addMessage(text, true);
//     //     this.messageInput.value = '';
//     //     this.updateCharCount();
//     //     this.messageInput.disabled = true;
//     //     this.sendBtn.disabled = true;
//     //     this.addTypingIndicator();

//     //     try {
//     //         let response;
            
//     //         if (window.chatBackend) {
//     //             // Use Python backend (bypasses CORS issues)
//     //             if (this.ragEnabled) {
//     //                 response = window.chatBackend.sendMessage(text, true);
//     //             } else {
//     //                 response = window.chatBackend.callOllama(text);
//     //             }
//     //         } else {
//     //             // Fallback to direct fetch (will fail in QWebEngine due to CORS)
//     //             response = await this.callOllama(text);
//     //         }

//     //         this.removeTypingIndicator();
//     //         if (response && response.trim()) {
//     //             this.addMessage(response, false);
//     //         } else {
//     //             this.showError('Empty response received');
//     //         }
//     //     } catch (error) {
//     //         this.removeTypingIndicator();
//     //         this.showError(`Error: ${error.message}`);
//     //     }

//     //     this.messageInput.disabled = false;
//     //     this.sendBtn.disabled = false;
//     //     this.messageInput.focus();
//     // }

//     async sendMessage() {
//         const text = this.messageInput.value.trim();
//         if (!text || text.length > 8000) return;

//         this.addMessage(text, true);
//         this.messageInput.value = '';
//         this.updateCharCount();
//         this.messageInput.disabled = true;
//         this.sendBtn.disabled = true;
//         this.addTypingIndicator();

//         try {
//             let response = '';
            
//             if (window.chatBackend) {
//                 // Use Python backend (bypasses CORS issues)
//                 if (this.ragEnabled) {
//                     response = window.chatBackend.sendMessage(text, true);
//                 } else {
//                     response = window.chatBackend.callOllama(text);
//                 }
                
//                 // Ensure response is a string
//                 if (typeof response !== 'string') {
//                     response = String(response || '');
//                 }
//             } else {
//                 // Fallback to direct fetch (will fail in QWebEngine due to CORS)
//                 response = await this.callOllama(text);
//             }

//             this.removeTypingIndicator();
            
//             const trimmedResponse = response.trim();
//             if (trimmedResponse && trimmedResponse.length > 0) {
//                 this.addMessage(trimmedResponse, false);
//             } else {
//                 this.showError('Empty or invalid response received');
//             }
//         } catch (error) {
//             this.removeTypingIndicator();
//             this.showError(`Error: ${error.message || String(error)}`);
//             console.error('Send message error:', error);
//         }

//         this.messageInput.disabled = false;
//         this.sendBtn.disabled = false;
//         this.messageInput.focus();
//     }



//     async callRagPipeline(prompt) {
//         try {
//             // Call Python backend synchronously
//             const response = window.chatBackend.sendMessage(prompt, this.ragEnabled);
//             return response || null;
//         } catch (error) {
//             console.error('RAG call failed:', error);
//             return null;
//         }
//     }

//     async callOllama(prompt) {
//         const response = await fetch(`${this.ollamaHost}/api/chat`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify({
//                 model: this.modelName,
//                 messages: [
//                     ...this.chatHistory.map(msg => ({
//                         role: msg.role,
//                         content: msg.content
//                     })),
//                     { role: 'user', content: prompt }
//                 ],
//                 stream: false
//             })
//         });

//         if (!response.ok) {
//             throw new Error(`HTTP ${response.status}: ${response.statusText}`);
//         }

//         const data = await response.json();
//         return data.message?.content || 'No response received';
//     }

//     // async checkConnection() {
//     //     try {
//     //         const response = await fetch(`${this.ollamaHost}/api/tags`, {
//     //             signal: AbortSignal.timeout(2000)
//     //         });

//     //         if (response.ok) {
//     //             const data = await response.json();
//     //             const models = data.models || [];
//     //             const hasModel = models.some(m => m.name.includes(this.modelName));

//     //             this.statusDot.classList.add('connected');
//     //             this.statusDot.classList.remove('offline');
//     //             this.statusText.textContent = hasModel ? 'Connected' : 'Model not found';
//     //             return hasModel;
//     //         } else {
//     //             throw new Error('Server error');
//     //         }
//     //     } catch (error) {
//     //         this.statusDot.classList.add('offline');
//     //         this.statusDot.classList.remove('connected');
//     //         this.statusText.textContent = 'Offline';
//     //         return false;
//     //     }
//     // }

//     // async checkConnection() {
//     //     try {
//     //         // Use Python backend to check connection (avoids CORS issues)
//     //         if (window.chatBackend) {
//     //             const connected = window.chatBackend.checkOllamaConnection();
//     //             if (connected) {
//     //                 this.statusDot.classList.add('connected');
//     //                 this.statusDot.classList.remove('offline');
//     //                 this.statusText.textContent = 'Connected';
//     //                 return true;
//     //             } else {
//     //                 throw new Error('Backend check failed');
//     //             }
//     //         }
            
//     //         // Fallback: manual timeout implementation
//     //         const controller = new AbortController();
//     //         const timeoutId = setTimeout(() => controller.abort(), 2000);
            
//     //         const response = await fetch(`${this.ollamaHost}/api/tags`, {
//     //             method: 'GET',
//     //             signal: controller.signal
//     //         });
            
//     //         clearTimeout(timeoutId);

//     //         if (response.ok) {
//     //             const data = await response.json();
//     //             const models = data.models || [];
//     //             const hasModel = models.some(m => m.name.includes(this.modelName));

//     //             this.statusDot.classList.add('connected');
//     //             this.statusDot.classList.remove('offline');
//     //             this.statusText.textContent = hasModel ? 'Connected' : 'Model not found';
//     //             return hasModel;
//     //         } else {
//     //             throw new Error('Server error');
//     //         }
//     //     } catch (error) {
//     //         console.error('Connection check failed:', error);
//     //         this.statusDot.classList.add('offline');
//     //         this.statusDot.classList.remove('connected');
//     //         this.statusText.textContent = 'Offline';
//     //         return false;
//     //     }
//     // }

//     async checkConnection() {
//         try {
//             // Use Python backend to check connection (avoids CORS issues)
//             if (window.chatBackend) {
//                 const status = window.chatBackend.checkOllamaConnection();
//                 if (status === 'connected') {
//                     this.statusDot.classList.add('connected');
//                     this.statusDot.classList.remove('offline');
//                     this.statusText.textContent = 'Connected';
//                     return true;
//                 } else {
//                     this.statusDot.classList.add('offline');
//                     this.statusDot.classList.remove('connected');
//                     this.statusText.textContent = 'Offline';
//                     return false;
//                 }
//             }
            
//             // Fallback: manual timeout implementation
//             const controller = new AbortController();
//             const timeoutId = setTimeout(() => controller.abort(), 2000);
            
//             const response = await fetch(`${this.ollamaHost}/api/tags`, {
//                 method: 'GET',
//                 signal: controller.signal
//             });
            
//             clearTimeout(timeoutId);

//             if (response.ok) {
//                 const data = await response.json();
//                 const models = data.models || [];
//                 const hasModel = models.some(m => m.name.includes(this.modelName));

//                 this.statusDot.classList.add('connected');
//                 this.statusDot.classList.remove('offline');
//                 this.statusText.textContent = hasModel ? 'Connected' : 'Model not found';
//                 return hasModel;
//             } else {
//                 throw new Error('Server error');
//             }
//         } catch (error) {
//             console.error('Connection check failed:', error);
//             this.statusDot.classList.add('offline');
//             this.statusDot.classList.remove('connected');
//             this.statusText.textContent = 'Offline';
//             return false;
//         }
//     }

//     clearChat() {
//         const confirmed = confirm('Clear all messages?');
//         if (confirmed) {
//             this.chatMessages.innerHTML = `
//                 <div class="welcome-message">
//                     <h2>Welcome to AI Assistant</h2>
//                     <p>Ask me anything about wind turbine analysis and data.</p>
//                 </div>
//             `;
//             this.chatHistory = [];
//         }
//     }

//     openSettings() {
//         document.getElementById('ollama_host').value = this.ollamaHost;
//         document.getElementById('model_select').value = this.modelName;
//         this.settingsModal.classList.add('show');
//     }

//     closeSettings() {
//         this.settingsModal.classList.remove('show');
//     }

//     saveSettings() {
//         this.ollamaHost = document.getElementById('ollama_host').value || 'http://localhost:11434';
//         this.modelName = document.getElementById('model_select').value;

//         localStorage.setItem('ollama_host', this.ollamaHost);
//         localStorage.setItem('model_name', this.modelName);

//         this.closeSettings();
//         this.checkConnection();
//     }

//     // async testConnection() {
//     //     const host = document.getElementById('ollama_host').value || 'http://localhost:11434';
//     //     try {
//     //         const response = await fetch(`${host}/api/tags`, {
//     //             signal: AbortSignal.timeout(3000)
//     //         });

//     //         if (response.ok) {
//     //             const data = await response.json();
//     //             const count = data.models?.length || 0;
//     //             alert(`✓ Connected successfully\nFound ${count} model(s)`);
//     //         } else {
//     //             alert(`✗ Connection failed: HTTP ${response.status}`);
//     //         }
//     //     } catch (error) {
//     //         alert(`✗ Connection failed:\n${error.message}`);
//     //     }
//     // }
//     async testConnection() {
//         const host = document.getElementById('ollama_host').value || 'http://localhost:11434';
        
//         // Use backend if available
//         if (window.chatBackend) {
//             const connected = window.chatBackend.checkOllamaConnection();
//             if (connected) {
//                 alert('✓ Connected successfully via Python backend');
//             } else {
//                 alert('✗ Connection failed - check console and ensure Ollama is running');
//             }
//             return;
//         }
        
//         // Fallback: manual timeout
//         try {
//             const controller = new AbortController();
//             const timeoutId = setTimeout(() => controller.abort(), 3000);
            
//             const response = await fetch(`${host}/api/tags`, {
//                 signal: controller.signal
//             });
            
//             clearTimeout(timeoutId);

//             if (response.ok) {
//                 const data = await response.json();
//                 const count = data.models?.length || 0;
//                 alert(`✓ Connected successfully\nFound ${count} model(s)`);
//             } else {
//                 alert(`✗ Connection failed: HTTP ${response.status}`);
//             }
//         } catch (error) {
//             alert(`✗ Connection failed:\n${error.message}`);
//         }
//     }


//     showError(message) {
//         const errorMsg = document.createElement('div');
//         errorMsg.className = 'message assistant';
//         errorMsg.innerHTML = `
//             <div class="message-avatar">!</div>
//             <div class="message-content">
//                 <div class="message-bubble" style="background: #fee; color: #c33;">
//                     ${message}
//                 </div>
//             </div>
//         `;
//         this.chatMessages.appendChild(errorMsg);
//         this.scrollToBottom();
//     }

//     scrollToBottom() {
//         this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
//     }

//     loadSettings() {
//         document.getElementById('ollama_host').value = this.ollamaHost;
//         document.getElementById('model_select').value = this.modelName;
//     }
// }

// // Initialize on page load
// document.addEventListener('DOMContentLoaded', () => {
//     new AIChatUI();
// });

class AIChatUI {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsModal = document.getElementById('settingsModal');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.charCount = document.getElementById('charCount');

        this.chatHistory = [];
        this.ollamaHost = localStorage.getItem('ollama_host') || 'http://localhost:11434';
        this.modelName = localStorage.getItem('model_name') || 'gemma4:e2b';
        this.ragEnabled = localStorage.getItem('rag_enabled') === 'true';
        this.isWaitingForResponse = false;

        this.setupEventListeners();
        this.loadSettings();
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.messageInput.addEventListener('input', () => this.updateCharCount());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.settingsBtn.addEventListener('click', () => this.openSettings());

        document.getElementById('closeSettings').addEventListener('click', () => this.closeSettings());
        document.getElementById('settingsCancel').addEventListener('click', () => this.closeSettings());
        document.getElementById('settingsSave').addEventListener('click', () => this.saveSettings());
        document.getElementById('testConnection').addEventListener('click', () => this.testConnection());

        const diagBtn = document.getElementById('diagBtn');
        if (diagBtn) {
            diagBtn.addEventListener('click', () => this.runDiagnostics());
        }
        const ragToggle = document.getElementById('ragToggle');
        if (ragToggle) {
            ragToggle.addEventListener('change', (e) => {
                this.ragEnabled = e.target.checked;
                localStorage.setItem('rag_enabled', this.ragEnabled);
            });
            ragToggle.checked = this.ragEnabled;
        }

        const indexBtn = document.getElementById('indexBtn');
        if (indexBtn) {
            indexBtn.addEventListener('click', () => this.indexDocuments());
        }

        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettings();
            }
        });
    }

    connectBackendSignals() {
        if (window.chatBackend) {
            // Connect to Python signals
            window.chatBackend.statusUpdate.connect((text) => {
                this.statusText.textContent = text;
                if (text.includes('Connected')) {
                    this.statusDot.classList.add('connected');
                    this.statusDot.classList.remove('offline');
                } else if (text.includes('Offline')) {
                    this.statusDot.classList.add('offline');
                    this.statusDot.classList.remove('connected');
                }
            });

            window.chatBackend.indexingComplete.connect((success) => {
                if (success) {
                    alert('✓ Documents indexed successfully');
                    this.ragEnabled = true;
                    const toggle = document.getElementById('ragToggle');
                    if (toggle) toggle.checked = true;
                } else {
                    alert('✗ Indexing failed — check the server logs');
                }
            });

            window.chatBackend.responseReceived.connect((text) => {
                this.removeTypingIndicator();
                this.addMessage(text, false);
                this.isWaitingForResponse = false;
                this.messageInput.disabled = false;
                this.sendBtn.disabled = false;
                this.messageInput.focus();
            });

            window.chatBackend.errorOccurred.connect((text) => {
                this.removeTypingIndicator();
                this.showError(text);
                this.isWaitingForResponse = false;
                this.messageInput.disabled = false;
                this.sendBtn.disabled = false;
                this.messageInput.focus();
            });

            window.chatBackend.connectionStatus.connect((connected) => {
                if (connected) {
                    this.statusDot.classList.add('connected');
                    this.statusDot.classList.remove('offline');
                } else {
                    this.statusDot.classList.add('offline');
                    this.statusDot.classList.remove('connected');
                }
            });

            // Initial connection check
            window.chatBackend.checkConnection();
        }
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count} / 8000`;

        if (count > 8000) {
            this.charCount.classList.add('warning');
            this.sendBtn.disabled = true;
        } else {
            this.charCount.classList.remove('warning');
            this.sendBtn.disabled = this.isWaitingForResponse;
        }
    }

    addMessage(text, isUser) {
        const message = document.createElement('div');
        message.className = `message ${isUser ? 'user' : 'assistant'}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = isUser ? 'U' : 'AI';

        const content = document.createElement('div');
        content.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        if (isUser) {
            bubble.textContent = text;
        } else {
            bubble.innerHTML = this.markdownToHtml(text);
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        content.appendChild(bubble);
        content.appendChild(time);

        if (isUser) {
            message.appendChild(content);
            message.appendChild(avatar);
        } else {
            message.appendChild(avatar);
            message.appendChild(content);
        }

        this.chatMessages.appendChild(message);
        this.scrollToBottom();

        const welcome = this.chatMessages.querySelector('.welcome-message');
        if (welcome && this.chatMessages.children.length > 1) {
            welcome.remove();
        }

        this.chatHistory.push({
            role: isUser ? 'user' : 'assistant',
            content: text,
            timestamp: new Date()
        });
    }

    markdownToHtml(text) {
        let html = text
            .replace(/&/g, '&')
            .replace(/</g, '<')
            .replace(/>/g, '>');

        html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    addTypingIndicator() {
        const message = document.createElement('div');
        message.className = 'message assistant';
        message.id = 'typing-indicator';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';

        const content = document.createElement('div');
        content.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble typing-indicator';
        bubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

        content.appendChild(bubble);
        message.appendChild(avatar);
        message.appendChild(content);

        this.chatMessages.appendChild(message);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typing = document.getElementById('typing-indicator');
        if (typing) {
            typing.remove();
        }
    }

    sendMessage() {
        const text = this.messageInput.value.trim();

        if (!text || text.length > 8000 || this.isWaitingForResponse) {
            return;
        }

        this.addMessage(text, true);
        this.messageInput.value = '';
        this.updateCharCount();

        this.messageInput.disabled = true;
        this.sendBtn.disabled = true;
        this.isWaitingForResponse = true;

        this.addTypingIndicator();

        // Send to Python backend via signal
        if (window.chatBackend) {
            window.chatBackend.sendMessage(text, this.ragEnabled);
        } else {
            this.removeTypingIndicator();
            this.showError('Backend not connected');
            this.isWaitingForResponse = false;
            this.messageInput.disabled = false;
            this.sendBtn.disabled = false;
        }
    }

    clearChat() {
        const confirmed = confirm('Clear all messages?');
        if (confirmed) {
            this.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h2>Welcome to AI Assistant</h2>
                    <p>Ask me anything about wind turbine analysis and data.</p>
                </div>
            `;
            this.chatHistory = [];
        }
    }

    openSettings() {
        document.getElementById('ollama_host').value = this.ollamaHost;
        document.getElementById('model_select').value = this.modelName;
        this.settingsModal.classList.add('show');
    }

    closeSettings() {
        this.settingsModal.classList.remove('show');
    }

    // REPLACE entire saveSettings method:
    saveSettings() {
        this.ollamaHost = document.getElementById('ollama_host').value || 'http://localhost:11434';
        this.modelName = document.getElementById('model_select').value;

        localStorage.setItem('ollama_host', this.ollamaHost);
        localStorage.setItem('model_name', this.modelName);

        this.closeSettings();

        if (window.chatBackend) {
            window.chatBackend.updateSettings(this.ollamaHost, this.modelName); // ADD THIS
            window.chatBackend.checkConnection();
        }
    }

    testConnection() {
        if (window.chatBackend) {
            window.chatBackend.checkConnection();
            setTimeout(() => {
                alert(`Status: ${this.statusText.textContent}`);
            }, 500);
        } else {
            alert('✗ Backend not connected');
        }
    }

    // indexDocuments() {
    //     if (!window.chatBackend) {
    //         alert('Backend not available');
    //         return;
    //     }

    //     const folder = prompt('Enter folder path to index:');
    //     if (!folder) return;

    //     const success = window.chatBackend.indexDocuments(folder);
        
    //     setTimeout(() => {
    //         if (success) {
    //             alert('✓ Documents indexed successfully');
    //             this.ragEnabled = true;
    //             const ragToggle = document.getElementById('ragToggle');
    //             if (ragToggle) ragToggle.checked = true;
    //         } else {
    //             alert('✗ Indexing failed - check console');
    //         }
    //     }, 1000);
    // }

    // REPLACE entire indexDocuments method:
    // REPLACE entire indexDocuments method:
    indexDocuments() {
        if (!window.chatBackend) {
            alert('Backend not available');
            return;
        }
        // Native Qt folder picker opens on the Python side
        // Result arrives via indexingComplete signal
        window.chatBackend.selectAndIndexDirectory();
    }

    showError(message) {
        const errorMsg = document.createElement('div');
        errorMsg.className = 'message assistant';
        errorMsg.innerHTML = `
            <div class="message-avatar">!</div>
            <div class="message-content">
                <div class="message-bubble" style="background: #fee; color: #c33;">
                    ${message}
                </div>
            </div>
        `;
        this.chatMessages.appendChild(errorMsg);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    loadSettings() {
        document.getElementById('ollama_host').value = this.ollamaHost;
        document.getElementById('model_select').value = this.modelName;
    }

    async runDiagnostics() {
        const host = this.ollamaHost;
        let report = `Ollama Diagnostics\n==================\n\n`;
        report += `Host: ${host}\n\n`;
        
        try {
            // Test 1: Check /api/tags
            report += `Test 1: GET ${host}/api/tags\n`;
            const tagsResponse = await fetch(`${host}/api/tags`, { 
                method: 'GET',
                signal: AbortSignal.timeout ? AbortSignal.timeout(3000) : undefined
            });
            report += `Status: ${tagsResponse.status}\n`;
            
            if (tagsResponse.ok) {
                const data = await tagsResponse.json();
                const models = data.models || [];
                report += `Models found: ${models.length}\n`;
                models.forEach(m => {
                    report += `  - ${m.name}\n`;
                });
            } else {
                report += `Error: ${tagsResponse.statusText}\n`;
            }
            report += `\n`;
            
            // Test 2: Check /api/version
            report += `Test 2: GET ${host}/api/version\n`;
            try {
                const versionResponse = await fetch(`${host}/api/version`, {
                    method: 'GET',
                    signal: AbortSignal.timeout ? AbortSignal.timeout(3000) : undefined
                });
                report += `Status: ${versionResponse.status}\n`;
                if (versionResponse.ok) {
                    const vdata = await versionResponse.json();
                    report += `Version: ${JSON.stringify(vdata)}\n`;
                }
            } catch (e) {
                report += `Failed: ${e.message}\n`;
            }
            report += `\n`;
            
            // Test 3: Try chat endpoint
            report += `Test 3: POST ${host}/api/chat\n`;
            try {
                const chatResponse = await fetch(`${host}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: this.modelName,
                        messages: [{ role: 'user', content: 'test' }],
                        stream: false
                    }),
                    signal: AbortSignal.timeout ? AbortSignal.timeout(5000) : undefined
                });
                report += `Status: ${chatResponse.status}\n`;
                if (!chatResponse.ok) {
                    report += `Error: ${chatResponse.statusText}\n`;
                    report += `Body: ${await chatResponse.text()}\n`;
                } else {
                    report += `Success!\n`;
                }
            } catch (e) {
                report += `Failed: ${e.message}\n`;
            }
            report += `\n`;
            
            report += `\nRecommendations:\n`;
            report += `1. Make sure Ollama is running: ollama serve\n`;
            report += `2. Pull the model: ollama pull ${this.modelName}\n`;
            report += `3. Check Ollama version: ollama --version\n`;
            report += `4. Try different model name if 404 persists\n`;
            
        } catch (error) {
            report += `\nFatal error: ${error.message}\n`;
        }
        
        // Show in alert or console
        console.log(report);
        alert(report);
    }
}

// Global instance
let chatUI;

document.addEventListener('DOMContentLoaded', () => {
    chatUI = new AIChatUI();
});