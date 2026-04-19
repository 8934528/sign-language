# Sign Language Detection System

A real-time sign language detection and translation system using computer vision and machine learning. This application captures hand gestures through your webcam and converts them into text, enabling basic non-verbal communication.

![Sign Language Detection](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-red.svg)

## Features

- **Real-time Gesture Recognition**: Detects and classifies hand gestures instantly using your webcam
- **Extended Alphabet Support**: Recognizes letters A-Z plus special gestures (👍, 🤘, 👌, ✋)
- **High Accuracy Detection**: Uses MediaPipe's advanced hand landmark detection
- **Confidence Scoring**: Shows detection confidence with visual indicators
- **Text Building**: Build words and sentences by combining gestures
- **Keyboard Shortcuts**: Full keyboard support for efficient use
- **Edge-to-Edge UI**: Modern, responsive interface that fills the entire screen
- **Live Statistics**: Real-time character and word count
- **Gesture Guide**: Built-in reference for all supported gestures

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- Windows/Linux/MacOS

### Installation

1. **Clone the repository**

        bash
        git clone https://github.com/yourusername/sign-language-detection.git
        cd sign-language-detection

2. Create virtual environment (recommended)

        bash
        python -m venv venv

        # On Windows
        venv/Scripts/activate

        # On Mac/Linux
        source venv/bin/activate

3. Install dependencies

        bash
        pip install -r requirements.txt

4. Run the application

        bash
        python app.py

5. Open your browser
Navigate to `http://localhost:5000`

## Usage

## Basic Controls

| Action         | Button          | Keyboard Shortcut |
|----------------|-----------------|-------------------|
| Add Gesture    | "Add" button    | Enter             |
| Add Space      | "Space" button  | Space             |
| Delete Last    | "Delete" button | Backspace         |
| Clear All      | "Clear" button  | Esc               |

## Supported Gestures

`**Letters**

- A: Closed fist
- B: Open palm with thumb tucked
- C: Curved hand shape
- D: Index finger up, thumb touching middle finger
- V: Peace sign (index and middle fingers)
- W: Three fingers up
- L: L-shape with thumb and index
- Y: Thumb and pinky extended

`**Special Gestures**

- 👍: Thumbs up
- 🤘: Rock sign (index and pinky)
- 👌: OK sign
- ✋: Open hand (stop)

`**Tips for Best Results**

1. Lighting: Ensure good, even lighting on your hand

2. Background: Use a plain, contrasting background

3. Distance: Keep your hand 12-18 inches from the camera

4. Position: Center your hand in the camera frame

5. Stability: Hold gestures steady for better recognition

---

## Project Structure

        sign-language/
        ├── app.py                 # Main Flask application
        ├── gesture_profiles.json
        ├── requirements.txt       # Python dependencies
        ├── .gitignore             # Git ignore file
        ├── README.md              # Documentation
        ├── static/
        │   ├── assets/
        │   ├── css/
        │   │   └── style.css      # Styling
        │   └── js/
        │       └── main.js        # Frontend logic
        └── templates/
            └── index.html         # Web interface

---

## Use Cases

- Education: Teaching sign language basics
- Accessibility: Basic communication tool
- Research: Gesture recognition studies
- Demo: Computer vision demonstrations
- Learning: Understanding ML/CV pipelines

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- **MediaPipe** by Google for hand tracking
- **OpenCV** community for computer vision tools
- **Flask** team for the lightweight web framework
- **Flaticon** for beautiful icons
