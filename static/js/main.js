class SignLanguageApp {
    constructor() {
        this.currentGesture = 'No gesture';
        this.lastGesture = '';
        this.gestureStability = 0;
        this.gestureHistory = [];
        this.stabilityThreshold = 3;
        this.confidenceScore = 0;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.startGestureMonitoring();
        this.startTextMonitoring();
        this.startTimeDisplay();
        this.animateConfidenceBar();
        
        console.log('Sign Language Detection System initialized');
    }

    setupEventListeners() {
        document.getElementById('addGestureBtn').addEventListener('click', () => this.addCurrentGesture());
        document.getElementById('addSpaceBtn').addEventListener('click', () => this.addSpace());
        document.getElementById('backspaceBtn').addEventListener('click', () => this.backspace());
        document.getElementById('clearTextBtn').addEventListener('click', () => this.clearText());
        
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        document.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('mousedown', (e) => e.preventDefault());
        });
    }

    handleKeyboard(event) {
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }

        switch(event.key) {
            case ' ':
                event.preventDefault();
                this.addSpace();
                break;
            case 'Backspace':
                event.preventDefault();
                this.backspace();
                break;
            case 'Enter':
                event.preventDefault();
                this.addCurrentGesture();
                break;
            case 'Escape':
                event.preventDefault();
                this.clearText();
                break;
            case 'c':
            case 'C':
                if (event.ctrlKey) {
                    event.preventDefault();
                    this.clearText();
                }
                break;
        }
    }

    async startGestureMonitoring() {
        const updateGesture = async () => {
            try {
                const response = await fetch('/get_gesture');
                const data = await response.json();
                
                if (data.gesture) {
                    this.processGesture(data.gesture);
                }
            } catch (error) {
                console.error('Error fetching gesture:', error);
                this.updateGestureDisplay('Error', 0);
            }
            
            setTimeout(updateGesture, 200); // 5 FPS for gesture updates
        };
        
        updateGesture();
    }

    processGesture(gesture) {
        this.gestureHistory.push(gesture);
        if (this.gestureHistory.length > 10) {
            this.gestureHistory.shift();
        }
        
        // gesture stability
        if (gesture === this.lastGesture) {
            this.gestureStability++;
        } else {
            this.gestureStability = 0;
            this.lastGesture = gesture;
        }
        
        this.confidenceScore = Math.min((this.gestureStability / this.stabilityThreshold) * 100, 100);
        
        // pdate display if gesture is stable 
        if (this.gestureStability >= this.stabilityThreshold || gesture !== this.currentGesture) {
            this.updateGestureDisplay(gesture, this.confidenceScore);
            
            if (this.gestureStability === this.stabilityThreshold && 
                gesture !== 'No hand detected' && 
                gesture !== 'Unknown' &&
                gesture !== 'Error') {
                this.autoAddGesture(gesture);
            }
        }
        
        // live overlay
        const liveGestureEl = document.getElementById('liveGesture');
        if (liveGestureEl) {
            liveGestureEl.textContent = gesture;
        }
    }

    updateGestureDisplay(gesture, confidence) {
        const gestureElement = document.getElementById('currentGesture');
        const confidenceBar = document.getElementById('confidenceBar');
        const gestureIcon = document.getElementById('gestureIcon');
        
        if (gestureElement) {
            if (gestureElement.textContent !== gesture) {
                gestureElement.textContent = gesture;
                gestureElement.classList.add('gesture-pop');
                setTimeout(() => {
                    gestureElement.classList.remove('gesture-pop');
                }, 500);
            }
        }
        
        if (confidenceBar) {
            confidenceBar.style.width = confidence + '%';
            
            // colour based on confidence
            if (confidence > 70) {
                confidenceBar.style.background = 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
            } else if (confidence > 40) {
                confidenceBar.style.background = 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)';
            } else {
                confidenceBar.style.background = 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
            }
        }
        
        if (gestureIcon) {
            this.updateGestureIcon(gestureIcon, gesture);
        }
        
        this.currentGesture = gesture;
    }

    updateGestureIcon(iconElement, gesture) {
        const iconMap = {
            'A': 'hand-fist',
            'B': 'hand',
            'C': 'hand-wave',
            'D': 'hand-pointing',
            'V': 'hand-peace',
            'W': 'hand-three',
            'L': 'hand-l-shape',
            'Y': 'hand-horns',
            '👍': 'hand-thumbs-up',
            '🤘': 'hand-horns',
            '👌': 'hand-ok',
            '✋': 'hand-palm'
        };
        
        const iconName = iconMap[gesture] || 'hand';
        iconElement.innerHTML = `<i class="fi fi-rr-${iconName}"></i>`;
    }

    async autoAddGesture(gesture) {
        if (this.confidenceScore > 80) {
            await this.addGesture(gesture);
        }
    }

    async addCurrentGesture() {
        if (this.currentGesture && 
            this.currentGesture !== 'No hand detected' && 
            this.currentGesture !== 'Unknown' &&
            this.currentGesture !== 'Error') {
            await this.addGesture(this.currentGesture);
        }
    }

    async addGesture(gesture) {
        try {
            const response = await fetch('/add_to_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ gesture: gesture })
            });
            
            if (response.ok) {
                this.showFeedback(`Added: ${gesture}`, 'success');
                await this.updateOutputText();
            }
        } catch (error) {
            console.error('Error adding gesture:', error);
            this.showFeedback('Failed to add gesture', 'error');
        }
    }

    async startTextMonitoring() {
        const updateText = async () => {
            await this.updateOutputText();
            setTimeout(updateText, 500);
        };
        
        updateText();
    }

    async updateOutputText() {
        try {
            const response = await fetch('/get_sentence');
            const data = await response.json();
            
            const outputElement = document.getElementById('outputText');
            const charCountEl = document.getElementById('charCount');
            const wordCountEl = document.getElementById('wordCount');
            
            if (outputElement) {
                outputElement.textContent = data.text || 'Ready to sign...';
            }
            
            if (charCountEl) {
                charCountEl.textContent = data.char_count || 0;
            }
            
            if (wordCountEl) {
                wordCountEl.textContent = data.word_count || 0;
            }
        } catch (error) {
            console.error('Error fetching text:', error);
        }
    }

    async clearText() {
        try {
            const response = await fetch('/clear_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                this.showFeedback('Text cleared', 'info');
                await this.updateOutputText();
            }
        } catch (error) {
            console.error('Error clearing text:', error);
        }
    }

    async addSpace() {
        try {
            const response = await fetch('/add_space', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                await this.updateOutputText();
            }
        } catch (error) {
            console.error('Error adding space:', error);
        }
    }

    async backspace() {
        try {
            const response = await fetch('/backspace', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                await this.updateOutputText();
            }
        } catch (error) {
            console.error('Error with backspace:', error);
        }
    }

    showFeedback(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `feedback-toast feedback-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#667eea'};
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 9999;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 2000);
    }

    startTimeDisplay() {
        const updateTime = () => {
            const timeEl = document.getElementById('currentTime');
            if (timeEl) {
                const now = new Date();
                timeEl.textContent = now.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            }
            setTimeout(updateTime, 1000);
        };
        
        updateTime();
    }

    animateConfidenceBar() {
        setInterval(() => {
            const bar = document.getElementById('confidenceBar');
            if (bar && parseFloat(bar.style.width) === 0) {
                bar.style.width = '5%';
                setTimeout(() => {
                    bar.style.width = '0%';
                }, 100);
            }
        }, 3000);
    }
}

// animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => {
    window.app = new SignLanguageApp();
});
