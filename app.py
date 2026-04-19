from flask import Flask, render_template, Response, jsonify, request
import cv2
import mediapipe as mp
import numpy as np
import threading
import time
import math
import base64

app = Flask(__name__)

# variables
current_gesture = "No gesture detected"
gesture_lock = threading.Lock()
latest_frame = None
frame_lock = threading.Lock()

class SignLanguageDetector:
    def __init__(self):
        self.current_word = []
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # mapping based on finger states
        self.gesture_map = {
            'A': 'A',
            'B': 'B', 
            'C': 'C',
            'D': 'D',
            'E': 'E',
            'F': 'F',
            'G': 'G',
            'H': 'H',
            'I': 'I',
            'K': 'K',
            'L': 'L',
            'Y': 'Y',
            'OK': 'OK',
            'PEACE': '✌',
            'THUMBS_UP': '👍',
            'THUMBS_DOWN': '👎',
            'ROCK': '🤘',
            'SPIDERMAN': '🕷️',
            'STOP': '✋'
        }
        
        # alphabet mapping
        self.alphabet_gestures = {
            'A': 'A',
            'B': 'B',
            'C': 'C',
            'D': 'D',
            'E': 'E',
            'F': 'F',
            'G': 'G',
            'H': 'H',
            'I': 'I',
            'J': 'J',
            'K': 'K',
            'L': 'L',
            'M': 'M',
            'N': 'N',
            'O': 'O',
            'P': 'P',
            'Q': 'Q',
            'R': 'R',
            'S': 'S',
            'T': 'T',
            'U': 'U',
            'V': 'V',
            'W': 'W',
            'X': 'X',
            'Y': 'Y',
            'Z': 'Z'
        }
    
    def get_finger_states(self, hand_landmarks):
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_pips = [3, 6, 10, 14, 18]
        
        fingers_up = []
        
        if hand_landmarks.landmark[finger_tips[0]].x > hand_landmarks.landmark[finger_pips[0]].x:
            fingers_up.append(1)
        else:
            fingers_up.append(0)
        
        # four fingers
        for tip, pip in zip(finger_tips[1:], finger_pips[1:]):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)
        
        return fingers_up
    
    def recognize_alphabet_gesture(self, hand_landmarks):
        fingers_up = self.get_finger_states(hand_landmarks)
        
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]
        ring_tip = hand_landmarks.landmark[16]
        pinky_tip = hand_landmarks.landmark[20]
        
        index_mcp = hand_landmarks.landmark[5]
        middle_mcp = hand_landmarks.landmark[9]
        ring_mcp = hand_landmarks.landmark[13]
        pinky_mcp = hand_landmarks.landmark[17]
        
        wrist = hand_landmarks.landmark[0]
        
        # Calculate distances and angles
        def distance(p1, p2):
            return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
        
        # match for letters
        # A: All fingers down, thumb across palm
        if fingers_up == [0, 0, 0, 0, 0]:
            return "A"
        
        # B: All fingers up, thumb across palm
        elif fingers_up == [0, 1, 1, 1, 1]:
            return "B"
        
        # C: Curved hand shape
        elif fingers_up[1:] == [1, 1, 1, 1] and distance(thumb_tip, index_tip) < 0.1:
            return "C"
        
        # D: Index up, others down, thumb touching middle
        elif fingers_up == [0, 1, 0, 0, 0] and distance(thumb_tip, middle_tip) < 0.05:
            return "D"
        
        # E: All fingers curled down
        elif fingers_up == [0, 0, 0, 0, 0] and index_tip.y > index_mcp.y:
            return "E"
        
        # F: Index and thumb touching, others up
        elif fingers_up == [0, 1, 1, 1, 0] and distance(thumb_tip, index_tip) < 0.03:
            return "F"
        
        # G: Index pointing, thumb extended
        elif fingers_up[1] == 1 and fingers_up[2:] == [0, 0, 0]:
            return "G"
        
        # H: Index and middle extended together
        elif fingers_up == [0, 1, 1, 0, 0] and distance(index_tip, middle_tip) < 0.03:
            return "H"
        
        # I: Pinky up only
        elif fingers_up == [0, 0, 0, 0, 1]:
            return "I"
        
        # K: Index and middle in V, thumb between
        elif fingers_up[1:3] == [1, 1] and fingers_up[3:] == [0, 0]:
            return "K"
        
        # L: Index and thumb in L shape
        elif fingers_up[:2] == [1, 1] and fingers_up[2:] == [0, 0, 0]:
            return "L"
        
        # V/Peace: Index and middle up, separated
        elif fingers_up == [0, 1, 1, 0, 0] and distance(index_tip, middle_tip) > 0.05:
            return "V"
        
        # W: Three fingers up (index, middle, ring)
        elif fingers_up == [0, 1, 1, 1, 0]:
            return "W"
        
        # Y: Thumb and pinky extended
        elif fingers_up == [1, 0, 0, 0, 1]:
            return "Y"
        
        # Thumbs up
        elif fingers_up == [1, 0, 0, 0, 0] and thumb_tip.y < wrist.y:
            return "👍"
        
        # Rock sign
        elif fingers_up == [0, 1, 0, 0, 1]:
            return "🤘"
        
        # OK sign
        elif distance(thumb_tip, index_tip) < 0.02 and fingers_up[2:] == [1, 1, 1]:
            return "👌"
        
        # Open hand (5)
        elif fingers_up == [1, 1, 1, 1, 1]:
            return "✋"
        
        else:
            return self.pattern_match_alphabet(fingers_up)
    
    def pattern_match_alphabet(self, fingers_up):
        patterns = {
            (0, 0, 0, 0, 0): "A/E",
            (0, 1, 1, 1, 1): "B",
            (0, 1, 0, 0, 0): "D",
            (0, 1, 1, 1, 0): "F/W",
            (0, 1, 1, 0, 0): "H/U",
            (0, 0, 0, 0, 1): "I/J",
            (1, 1, 0, 0, 0): "L",
            (1, 1, 1, 1, 1): "OPEN",
        }
        return patterns.get(tuple(fingers_up), "Unknown")
    
    def detect_gesture(self, frame):
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if not results.multi_hand_landmarks:
                return "No hand detected"
            
            # process first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # recognize gesture
            gesture = self.recognize_alphabet_gesture(hand_landmarks)
            
            # map to display format
            display_gesture = self.gesture_map.get(gesture, gesture)
            
            return display_gesture
            
        except Exception as e:
            print(f"Detection error: {e}")
            return "Error"
    
    def draw_gesture_info(self, frame, gesture):
        display_frame = frame.copy()
        
        # convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # landmarks
                self.mp_drawing.draw_landmarks(
                    display_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # bounding box
                h, w, _ = frame.shape
                x_min = int(min([lm.x for lm in hand_landmarks.landmark]) * w) - 20
                x_max = int(max([lm.x for lm in hand_landmarks.landmark]) * w) + 20
                y_min = int(min([lm.y for lm in hand_landmarks.landmark]) * h) - 20
                y_max = int(max([lm.y for lm in hand_landmarks.landmark]) * h) + 20
                
                cv2.rectangle(display_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # gesture text with background
        text = f"Gesture: {gesture}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        # text background
        cv2.rectangle(display_frame, 
                     (5, 5), 
                     (15 + text_width, 15 + text_height + 10), 
                     (0, 0, 0), -1)
        
        # text
        cv2.putText(display_frame, text, (10, 35), 
                   font, font_scale, (0, 255, 0), thickness)
        
        # instruction text
        cv2.putText(display_frame, "Press SPACE to add | ENTER to confirm", 
                   (10, display_frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display_frame

detector = SignLanguageDetector()

def camera_thread():
    global latest_frame, current_gesture
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frame_count = 0
    process_every_n_frames = 2  #process every 2nd frame 
    
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
        
        # Compress frame
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
    
    if gesture and gesture not in ['Unknown', 'No hand detected', 'No gesture detected', 'Error', 'A/E', 'F/W', 'H/U', 'I/J']:
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
    # Statr camera
    camera_thread = threading.Thread(target=camera_thread, daemon=True)
    camera_thread.start()
    
    print("\n" + "="*50)
    print(" Sign Language Detection System")
    print("="*50)
    print("\nCamera initialized")
    print("MediaPipe Hands loaded")
    print("Gesture recognition active")
    print("\nServer starting at: http://localhost:5000")
    print("\nControls:")
    print("  • Show hand gesture to camera")
    print("  • Press SPACE to add gesture to text")
    print("  • Press ENTER to confirm and continue")
    print("  • Press BACKSPACE to delete last character")
    print("  • Press ESC to clear all text")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
