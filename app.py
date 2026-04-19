from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import threading
import time
import math

app = Flask(__name__)

current_gesture = "No gesture detected"
gesture_lock = threading.Lock()
latest_frame = None
frame_lock = threading.Lock()

class SignLanguageDetector:
    def __init__(self):
        self.current_word = []
        self.gesture_map = {
            'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E',
            'F': 'F', 'V': 'V', 'W': 'W', 'L': 'L', 'Y': 'Y',
            'OK': 'OK', 'PEACE': '✌', 'THUMBS_UP': '👍',
            'ROCK': '🤘', 'STOP': '✋'
        }
    
    def calculate_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def detect_gesture(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return "No hand detected"
            
            hand_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(hand_contour) < 5000:
                return "No hand detected"
            
            hull = cv2.convexHull(hand_contour, returnPoints=False)
            
            if len(hull) < 3:
                return "A"
            
            defects = cv2.convexityDefects(hand_contour, hull)
            
            if defects is None:
                return "A"
            
            finger_count = 0
            
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(hand_contour[s][0])
                end = tuple(hand_contour[e][0])
                far = tuple(hand_contour[f][0])
                
                a = self.calculate_distance(end, start)
                b = self.calculate_distance(far, start)
                c = self.calculate_distance(end, far)
                
                if b * c == 0:
                    continue
                    
                angle = math.acos((b**2 + c**2 - a**2) / (2 * b * c)) * 180 / math.pi
                
                if angle <= 90 and d > 10000:
                    finger_count += 1
            
            if finger_count == 0:
                return "A"
            elif finger_count == 1:
                return "B"
            elif finger_count == 2:
                return "C"
            elif finger_count == 3:
                return "D"
            elif finger_count == 4:
                return "E"
            elif finger_count >= 5:
                return "F"
            else:
                return "Unknown"
                
        except Exception as e:
            print(f"Detection error: {e}")
            return "Error"
    
    def draw_gesture_info(self, frame, gesture):
        display_frame = frame.copy()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            hand_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(hand_contour) > 5000:
                cv2.drawContours(display_frame, [hand_contour], -1, (0, 255, 0), 2)
                
                hull = cv2.convexHull(hand_contour)
                cv2.drawContours(display_frame, [hull], -1, (255, 0, 0), 2)
                
                x, y, w, h = cv2.boundingRect(hand_contour)
                cv2.rectangle(display_frame, (x-10, y-10), (x+w+10, y+h+10), (0, 255, 255), 2)
        
        text = f"Gesture: {gesture}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        cv2.rectangle(display_frame, (5, 5), (15 + text_width, 15 + text_height + 10), (0, 0, 0), -1)
        cv2.putText(display_frame, text, (10, 35), font, font_scale, (0, 255, 0), thickness)
        cv2.putText(display_frame, "SPACE: Add | ENTER: Confirm | ESC: Clear", 
                   (10, display_frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display_frame

detector = SignLanguageDetector()

def camera_thread():
    global latest_frame, current_gesture
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frame_count = 0
    process_every_n_frames = 2
    
    while True:
        success, frame = cap.read()
        if not success:
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera Error - Please check connection", 
                       (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            frame = cv2.flip(frame, 1)
            
            if frame_count % process_every_n_frames == 0:
                gesture = detector.detect_gesture(frame)
                with gesture_lock:
                    current_gesture = gesture
            
            frame = detector.draw_gesture_info(frame, current_gesture)
            frame_count += 1
        
        with frame_lock:
            latest_frame = frame
            
        time.sleep(0.01)
    
    cap.release()

def generate_frames():
    while True:
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()
            else:
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                cv2.putText(frame, "Starting camera...", 
                           (50, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_gesture')
def get_gesture():
    with gesture_lock:
        gesture = current_gesture
    return jsonify({'gesture': gesture})

@app.route('/add_to_text', methods=['POST'])
def add_to_text():
    data = request.get_json()
    gesture = data.get('gesture', '') if data else ''
    
    if gesture and gesture not in ['Unknown', 'No hand detected', 'No gesture detected', 'Error']:
        detector.current_word.append(gesture)
        if len(detector.current_word) > 50:
            detector.current_word = detector.current_word[-50:]
    
    return jsonify({'success': True})

@app.route('/clear_text', methods=['POST'])
def clear_text():
    detector.current_word = []
    return jsonify({'success': True})

@app.route('/get_current_text')
def get_current_text():
    current_text = ''.join(detector.current_word) if detector.current_word else "Ready to sign..."
    return jsonify({'text': current_text})

@app.route('/add_space', methods=['POST'])
def add_space():
    detector.current_word.append(' ')
    return jsonify({'success': True})

@app.route('/backspace', methods=['POST'])
def backspace():
    if detector.current_word:
        detector.current_word.pop()
    return jsonify({'success': True})

@app.route('/get_sentence')
def get_sentence():
    sentence = ''.join(detector.current_word)
    words = sentence.split()
    return jsonify({
        'text': sentence,
        'word_count': len(words),
        'char_count': len(sentence)
    })

if __name__ == '__main__':
    camera_thread = threading.Thread(target=camera_thread, daemon=True)
    camera_thread.start()
    
    print("\n" + "="*50)
    print(" Sign Language Detection System")
    print("="*50)
    print("\nCamera initialized")
    print("OpenCV detection active")
    print("Gesture recognition active")
    print("\nServer starting at: http://localhost:5000")
    print("\nControls:")
    print("  - Show hand gesture to camera")
    print("  - Press SPACE to add gesture to text")
    print("  - Press ENTER to confirm and continue")
    print("  - Press BACKSPACE to delete last character")
    print("  - Press ESC to clear all text")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
