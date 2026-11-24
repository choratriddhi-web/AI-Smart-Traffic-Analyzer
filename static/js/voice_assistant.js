// Web Speech API Voice Assistant & Conversational Bot

class AIVoiceAssistant {
    constructor() {
        this.recognition = null;
        this.synth = window.speechSynthesis || null;
        this.isListening = false;
        this.chatBox = document.getElementById('chat-messages');
        this.micBtn = document.getElementById('btn-mic-toggle');
        this.inputField = document.getElementById('chat-input-field');
        this.sendBtn = document.getElementById('btn-chat-send');
        this.statusIndicator = document.getElementById('mic-status-indicator');

        this.initSpeechRecognition();
        this.bindEvents();
    }

    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                this.isListening = true;
                this.updateMicUI(true);
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                if (transcript) {
                    this.appendMessage('user', transcript);
                    this.queryBackend(transcript);
                }
            };

            this.recognition.onerror = (event) => {
                console.warn('Speech recognition error:', event.error);
                this.updateMicUI(false);
                if (event.error === 'not-allowed') {
                    this.appendMessage('bot', 'Microphone permission was denied. Please allow microphone access or use text input.');
                }
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.updateMicUI(false);
            };
        } else {
            console.warn('Web Speech API is not supported in this browser. Falling back to text-only mode.');
            if (this.statusIndicator) {
                this.statusIndicator.textContent = 'Voice input not supported in this browser; text mode active.';
            }
        }
    }

    bindEvents() {
        if (this.micBtn) {
            this.micBtn.addEventListener('click', () => {
                this.toggleListening();
            });
        }

        if (this.sendBtn && this.inputField) {
            this.sendBtn.addEventListener('click', () => {
                this.sendTextMessage();
            });

            this.inputField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendTextMessage();
                }
            });
        }
    }

    toggleListening() {
        if (!this.recognition) {
            alert('Voice recognition is not supported in your current browser. You can type questions in the chat input below.');
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (e) {
                console.error(e);
            }
        }
    }

    updateMicUI(listening) {
        if (!this.micBtn) return;
        if (listening) {
            this.micBtn.classList.add('btn-danger');
            this.micBtn.classList.remove('btn-purple');
            this.micBtn.innerHTML = '<i class="bi bi-mic-fill animate-pulse"></i> Listening...';
            if (this.statusIndicator) this.statusIndicator.textContent = 'Listening... Speak your traffic question.';
        } else {
            this.micBtn.classList.remove('btn-danger');
            this.micBtn.classList.add('btn-purple');
            this.micBtn.innerHTML = '<i class="bi bi-mic-fill"></i> Speak';
            if (this.statusIndicator) this.statusIndicator.textContent = 'Click Speak or type your question below.';
        }
    }

    sendTextMessage() {
        const text = this.inputField.value.trim();
        if (!text) return;
        this.appendMessage('user', text);
        this.inputField.value = '';
        this.queryBackend(text);
    }

    appendMessage(sender, text) {
        if (!this.chatBox) return;
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;

        const icon = sender === 'user'
            ? '<i class="bi bi-person-fill me-1 text-cyan"></i> '
            : '<i class="bi bi-robot me-1 text-purple"></i> ';

        bubble.innerHTML = `${icon}<span>${text.replace(/\n/g, '<br>')}</span>`;
        this.chatBox.appendChild(bubble);
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    }

    async queryBackend(question) {
        try {
            const resp = await fetch('/assistant/api/query/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ query: question })
            });

            const data = await resp.json();
            if (data.status === 'success') {
                this.appendMessage('bot', data.answer);
                this.speak(data.answer);
            } else {
                const errMsg = data.message || 'Could not retrieve traffic telemetry.';
                this.appendMessage('bot', errMsg);
            }
        } catch (e) {
            console.error('API query error:', e);
            this.appendMessage('bot', 'Network communication error. Please ensure Django server is running.');
        }
    }

    speak(text) {
        if (!this.synth) return;
        try {
            this.synth.cancel(); // Stop prior speech
            // Clean text of bullets and special chars for clean spoken voice
            const cleanText = text.replace(/[*#•]/g, '').replace(/https?:\/\/\S+/g, '');
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.lang = 'en-US';
            this.synth.speak(utterance);
        } catch (e) {
            console.warn('Speech synthesis failed:', e);
        }
    }

    getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('chat-messages')) {
        window.aiVoiceAssistant = new AIVoiceAssistant();
    }
});
