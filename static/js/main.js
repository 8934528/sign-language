class SignLanguageApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startGestureMonitoring();
        this.startTextMonitoring();
    }

    setupEventListeners() {
        document.getElementById('addGesture').addEventListener('click', () => this.addCurrentGesture());
        document.getElementById('clearText').addEventListener('click', () => this.clearText());
        document.getElementById('addSpace').addEventListener('click', () => this.addSpace());
        document.getElementById('backspace').addEventListener('click', () => this.backspace());
        
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    handleKeyboard(event) {
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
        }
    }

    async startGestureMonitoring() {
        setInterval(async () => {
            try {
                const response = await fetch('/get_gesture');
                const data = await response.json();
                this.updateCurrentGesture(data.gesture);
            } catch (error) {
                this.updateCurrentGesture('Error');
            }
        }, 500);
    }

    async startTextMonitoring() {
        setInterval(async () => {
            await this.updateOutputText();
        }, 1000);
    }

    updateCurrentGesture(gesture) {
        const gestureElement = document.getElementById('currentGesture');
        
        if (gestureElement.textContent !== gesture) {
            gestureElement.textContent = gesture;
            gestureElement.classList.add('gesture-pop');
            
            setTimeout(() => {
                gestureElement.classList.remove('gesture-pop');
            }, 500);
        }
    }

    async addCurrentGesture() {
        const gestureElement = document.getElementById('currentGesture');
        const gesture = gestureElement.textContent;
        
        if (gesture && gesture !== 'No hand detected' && gesture !== 'Unknown' && gesture !== 'Error') {
            try {
                await fetch('/add_to_text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ gesture: gesture })
                });
            } catch (error) {
                console.error('Error adding gesture:', error);
            }
        }
    }

    async updateOutputText() {
        try {
            const response = await fetch('/get_current_text');
            const data = await response.json();
            document.getElementById('outputText').textContent = data.text;
        } catch (error) {
            console.error('Error fetching text:', error);
        }
    }

    async clearText() {
        try {
            await fetch('/clear_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.error('Error clearing text:', error);
        }
    }

    async addSpace() {
        try {
            await fetch('/add_space', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.error('Error adding space:', error);
        }
    }

    async backspace() {
        try {
            await fetch('/backspace', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.error('Error with backspace:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SignLanguageApp();
});