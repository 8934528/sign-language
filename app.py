from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import threading
import time
import math
import json
import os

app = Flask(__name__)

current_gesture = "No gesture detected"
current_location = "unknown"
current_movement = "stationary"
current_orientation = "unknown"
current_confidence = 0

gesture_lock = threading.Lock()
latest_frame = None
frame_lock = threading.Lock()

class GestureProfile:
    def __init__(self):
        self.profiles_file = "gesture_profiles.json"
        self.load_profiles()
    
    def save_profile(self, gesture_name, finger_count, area_range, aspect_range):
        profile = {
            'finger_count': finger_count,
            'min_area': area_range[0],
            'max_area': area_range[1],
            'min_aspect': aspect_range[0],
            'max_aspect': aspect_range[1]
        }
        self.profiles[gesture_name] = profile
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
        return True
    
    def load_profiles(self):
        if os.path.exists(self.profiles_file):
            with open(self.profiles_file, 'r') as f:
                self.profiles = json.load(f)
        else:
            self.profiles = {}
    
    def match_profile(self, finger_count, area, aspect_ratio):
        for gesture, profile in self.profiles.items():
            if profile['finger_count'] == finger_count:
                if profile['min_area'] <= area <= profile['max_area']:
                    if profile['min_aspect'] <= aspect_ratio <= profile['max_aspect']:
                        return gesture
        return None

class SignLanguageDetector:
    def __init__(self):
        self.current_word = []
        self.gesture_map = {
            'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E',
            'F': 'F', 'V': 'V', 'W': 'W', 'L': 'L', 'Y': 'Y',
            'OK': 'OK', 'PEACE': '✌', 'THUMBS_UP': '👍',
            'ROCK': '🤘', 'STOP': '✋'
        }
        
        self.prev_position = None
        self.movement_history = []
        self.movement_direction = "stationary"
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        self.profile_manager = GestureProfile()
    
    def calculate_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def detect_skin(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_mask = cv2.GaussianBlur(skin_mask, (5, 5), 0)
        return skin_mask
    
    def isolate_hand(self, frame):
        fg_mask = self.bg_subtractor.apply(frame)
        kernel = np.ones((5,5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        return fg_mask
    
    def detect_location(self, hand_contour, frame_shape):
        h, w = frame_shape[:2]
        M = cv2.moments(hand_contour)
        if M['m00'] == 0:
            return "unknown"
        
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        
        if cy < h * 0.25:
            return "head"
        elif cy < h * 0.45:
            return "chest"
        elif cy < h * 0.65:
            return "waist"
        else:
            return "lower"
    
    def detect_movement(self, hand_contour):
        M = cv2.moments(hand_contour)
        if M['m00'] == 0:
            return self.movement_direction
        
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        current_pos = (cx, cy)
        
        if self.prev_position:
            dx = current_pos[0] - self.prev_position[0]
            dy = current_pos[1] - self.prev_position[1]
            
            if abs(dx) < 20 and abs(dy) < 20:
                self.movement_direction = "stationary"
            elif abs(dx) > abs(dy):
                self.movement_direction = "right" if dx > 0 else "left"
            else:
                self.movement_direction = "down" if dy > 0 else "up"
            
            self.movement_history.append(self.movement_direction)
            if len(self.movement_history) > 10:
                self.movement_history.pop(0)
        
        self.prev_position = current_pos
        return self.movement_direction
    
    def detect_palm_orientation(self, hand_contour):
        if len(hand_contour) < 5:
            return "unknown"
        
        rect = cv2.minAreaRect(hand_contour)
        angle = rect[2]
        width, height = rect[1]
        
        if width < 1 or height < 1:
            return "unknown"
        
        if angle < -45:
            return "down"
        elif angle > 45:
            return "up"
        elif width > height:
            return "sideways"
        else:
            return "forward"
    
    def calculate_hand_size(self, hand_contour):
        area = cv2.contourArea(hand_contour)
        rect = cv2.minAreaRect(hand_contour)
        width, height = rect[1]
        aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1
        return area, aspect_ratio
    
    def calculate_confidence(self, finger_count, hand_contour):
        area = cv2.contourArea(hand_contour)
        hull = cv2.convexHull(hand_contour)
        hull_area = cv2.contourArea(hull)
        
        if hull_area == 0:
            return 0
        
        solidity = area / hull_area
        rect = cv2.minAreaRect(hand_contour)
        _, (w, h), _ = rect
        aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 1
        
        confidence = solidity * 70 + (1 / aspect_ratio) * 30
        return min(100, int(confidence))
    
    def detect_single_gesture(self, hand_contour):
        hull = cv2.convexHull(hand_contour, returnPoints=False)
        
        if len(hull) < 3:
            return "A", 0
        
        defects = cv2.convexityDefects(hand_contour, hull)
        
        if defects is None:
            return "A", 0
        
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
        
        area, aspect_ratio = self.calculate_hand_size(hand_contour)
        confidence = self.calculate_confidence(finger_count, hand_contour)
        
        profiled_gesture = self.profile_manager.match_profile(finger_count, area, aspect_ratio)
        if profiled_gesture:
            return profiled_gesture, confidence
        
        if finger_count == 0:
            return "A", confidence
        elif finger_count == 1:
            return "B", confidence
        elif finger_count == 2:
            return "C", confidence
        elif finger_count == 3:
            return "D", confidence
        elif finger_count == 4:
            return "E", confidence
        elif finger_count >= 5:
            return "F", confidence
        else:
            return "Unknown", confidence
    
    def detect_gestures_multi(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        hands = []
        for contour in contours:
            if cv2.contourArea(contour) > 5000:
                gesture, conf = self.detect_single_gesture(contour)
                hands.append({'gesture': gesture, 'confidence': conf})
        
        return hands
    
    def detect_gesture(self, frame):
        global current_location, current_movement, current_orientation, current_confidence
        
        try:
            skin_mask = self.detect_skin(frame)
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
            
            combined = cv2.bitwise_and(thresh, skin_mask)
            
            contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                current_location = "unknown"
                current_movement = "stationary"
                current_orientation = "unknown"
                current_confidence = 0
                return "No hand detected"
            
            hand_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(hand_contour) < 3000:
                current_location = "unknown"
                current_movement = "stationary"
                current_orientation = "unknown"
                current_confidence = 0
                return "No hand detected"
            
            current_location = self.detect_location(hand_contour, frame.shape)
            current_movement = self.detect_movement(hand_contour)
            current_orientation = self.detect_palm_orientation(hand_contour)
            
            gesture, confidence = self.detect_single_gesture(hand_contour)
            current_confidence = confidence
            
            return gesture
                
        except Exception as e:
            print(f"Detection error: {e}")
            current_location = "unknown"
            current_movement = "stationary"
            current_orientation = "unknown"
            current_confidence = 0
            return "Error"
    
    def draw_gesture_info(self, frame, gesture):
        display_frame = frame.copy()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            hand_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(hand_contour) > 3000:
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
        
        y_offset = 70
        cv2.putText(display_frame, f"Loc: {current_location}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Mov: {current_movement}", (10, y_offset + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Ori: {current_orientation}", (10, y_offset + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Conf: {current_confidence}%", (10, y_offset + 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
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
    process_every_n_frames = 1
    
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
            
        time.sleep(0.03)
    
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

@app.route('/get_location')
def get_location():
    return jsonify({'location': current_location})

@app.route('/get_movement')
def get_movement():
    return jsonify({'movement': current_movement})

@app.route('/get_orientation')
def get_orientation():
    return jsonify({'orientation': current_orientation})

@app.route('/get_all_features')
def get_all_features():
    return jsonify({
        'gesture': current_gesture,
        'location': current_location,
        'movement': current_movement,
        'orientation': current_orientation,
        'confidence': current_confidence
    })

@app.route('/save_profile', methods=['POST'])
def save_profile():
    data = request.get_json()
    gesture_name = data.get('gesture')
    finger_count = data.get('finger_count')
    area_range = data.get('area_range', [0, 100000])
    aspect_range = data.get('aspect_range', [1, 5])
    
    if gesture_name and finger_count is not None:
        detector.profile_manager.save_profile(gesture_name, finger_count, area_range, aspect_range)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid data'})

@app.route('/get_profiles')
def get_profiles():
    return jsonify({'profiles': detector.profile_manager.profiles})

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
    time.sleep(2)
    
    print("\n" + "="*50)
    print(" Sign Language Detection System")
    print("="*50)
    print("\nCamera initialized")
    print("OpenCV detection active")
    print("Gesture recognition active")
    print("\nFeatures enabled:")
    print("  • Hand shape detection (A-F)")
    print("  • Location tracking")
    print("  • Movement detection")
    print("  • Palm orientation")
    print("  • Confidence scoring")
    print("  • Skin color detection")
    print("\nServer starting at: http://localhost:5000")
    print("\nControls:")
    print("  • Show hand gesture to camera")
    print("  • Press SPACE to add gesture to text")
    print("  • Press ENTER to confirm and continue")
    print("  • Press BACKSPACE to delete last character")
    print("  • Press ESC to clear all text")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
