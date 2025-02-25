import cv2
import mediapipe as mp
import time
from PyQt5.QtCore import QObject, pyqtSignal

class GestureController(QObject):
    frame_processed = pyqtSignal(object)
    gesture_detected = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.running = True
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.prev_x = None
        self.last_swipe_time = 0
        self.cooldown = 0.5

    def start_capture(self):
        cap = cv2.VideoCapture(0)
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            self.process_frame(frame)
            self.frame_processed.emit(frame)

        cap.release()
        self.hands.close()

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            index_finger_x = hand_landmarks.landmark[8].x
            current_time = time.time()

            if self.prev_x is not None and (current_time - self.last_swipe_time) > self.cooldown:
                delta_x = index_finger_x - self.prev_x
                if delta_x > 0.05:
                    self.gesture_detected.emit(1)
                    self.last_swipe_time = current_time
                elif delta_x < -0.05:
                    self.gesture_detected.emit(-1)
                    self.last_swipe_time = current_time

            self.prev_x = index_finger_x
            self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

    def stop(self):
        self.running = False