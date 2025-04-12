import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS
                    )
        return img

    def get_hand_position(self, img):
        hand_position = {'center_x': 0, 'center_y': 0}
        
        if self.results.multi_hand_landmarks:
            hand_landmarks = self.results.multi_hand_landmarks[0]
            h, w, c = img.shape
            
            # Calculate center of hand using palm landmarks
            x_coordinates = []
            y_coordinates = []
            for landmark in hand_landmarks.landmark:
                x_coordinates.append(landmark.x * w)
                y_coordinates.append(landmark.y * h)
            
            hand_position['center_x'] = int(sum(x_coordinates) / len(x_coordinates))
            hand_position['center_y'] = int(sum(y_coordinates) / len(y_coordinates))
            
        return hand_position

    def get_finger_direction(self, img):
        direction = {'x': None, 'y': None}
        
        if self.results.multi_hand_landmarks:
            hand_landmarks = self.results.multi_hand_landmarks[0]
            h, w, c = img.shape
            
            # Get index finger tip and base positions
            index_tip = hand_landmarks.landmark[8]
            index_base = hand_landmarks.landmark[5]
            
            # Calculate direction
            dx = index_tip.x - index_base.x
            dy = index_tip.y - index_base.y
            
            # Set threshold for movement
            threshold = 0.02
            
            if abs(dx) > threshold:
                direction['x'] = 1 if dx > 0 else -1
            
            if abs(dy) > threshold:
                direction['y'] = 1 if dy > 0 else -1
                
        return direction