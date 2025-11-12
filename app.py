from flask import Flask, render_template, Response, jsonify, request
import cv2
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
            
            if cv2.contourArea(hand_contour) < 1000:
                return "No hand detected"
            
            hull = cv2.convexHull(hand_contour, returnPoints=False)
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
            return "Unknown"
    
    def draw_gesture_info(self, frame, gesture):
        display_frame = frame.copy()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            hand_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(hand_contour) > 1000:
                cv2.drawContours(display_frame, [hand_contour], -1, (0, 255, 0), 2)
        
        cv2.putText(display_frame, f"Gesture: {gesture}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return display_frame

detector = SignLanguageDetector()

def camera_thread():
    global latest_frame, current_gesture
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    while True:
        success, frame = cap.read()
        if not success:
            frame = cv2.putText(
                cv2.zeros((480, 640, 3), dtype='uint8'), 
                "Camera Error", 
                (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
            )
        else:
            frame = cv2.flip(frame, 1)
            gesture = detector.detect_gesture(frame)
            
            with gesture_lock:
                current_gesture = gesture
            
            frame = detector.draw_gesture_info(frame, gesture)
        
        with frame_lock:
            latest_frame = frame
            
        time.sleep(0.03)
    
    cap.release()

def generate_frames():
    while True:
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()
            else:
                frame = cv2.putText(
                    cv2.zeros((480, 640, 3), dtype='uint8'),
                    "Loading camera...", 
                    (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
                )
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            frame_bytes = buffer.tobytes()
        else:
            frame_bytes = b''
        
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
    
    if gesture and gesture not in ['Unknown', 'No hand detected', 'No gesture detected']:
        detector.current_word.append(gesture)
        if len(detector.current_word) > 20:
            detector.current_word = detector.current_word[-20:]
    
    return jsonify({'success': True})

@app.route('/clear_text', methods=['POST'])
def clear_text():
    detector.current_word = []
    return jsonify({'success': True})

@app.route('/get_current_text')
def get_current_text():
    current_text = ''.join(detector.current_word) if detector.current_word else "Start signing..."
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

if __name__ == '__main__':
    camera_thread = threading.Thread(target=camera_thread, daemon=True)
    camera_thread.start()
    time.sleep(2)
    print("Server starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)