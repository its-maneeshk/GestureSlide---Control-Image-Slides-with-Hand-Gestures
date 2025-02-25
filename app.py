import cv2
import mediapipe as mp
import sys
import os
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QEvent, QPoint, pyqtSignal, QObject, QSize
from PyQt5.QtWidgets import QFileDialog

# Initialize MediaPipe Hand module
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

class DraggableVideoLabel(QLabel):
    """A QLabel that acts as a draggable floating video window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 100)
        self.setStyleSheet("border: 2px solid gray; border-radius: 5px; background-color: black;")
        self.dragging = False
        self.offset = QPoint(0, 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.raise_()

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            parent_rect = self.parent().rect()
            new_x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
            new_y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))
            self.move(new_x, new_y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

class ImageSlider(QWidget):
    change_image_requested = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.image_folder = self.select_image_folder()  # Let user select folder
        if not self.image_folder:
            sys.exit("No folder selected. Exiting application.")
        self.image_files = self.load_image_files()
        self.current_index = 0
        self.main_pixmaps = []
        self.selected_thumb_pixmaps = []
        self.unselected_thumb_pixmaps = []
        self.preload_images()
        self.initUI()
        self.start_gesture_recognition()

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        return folder
    
    def load_image_files(self):
        files = [os.path.join(self.image_folder, f) 
                for f in os.listdir(self.image_folder) 
                if f.lower().endswith(("png", "jpg", "jpeg"))]
        files.sort()
        return files

    def preload_images(self):
        for img_path in self.image_files:
            main_pix = QPixmap(img_path)
            self.main_pixmaps.append(main_pix)
            self.selected_thumb_pixmaps.append(
                main_pix.scaled(100, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.unselected_thumb_pixmaps.append(
                main_pix.scaled(80, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def initUI(self):
        self.setWindowTitle("GestureSlide - Image Slider")
        self.setGeometry(100, 100, 900, 600)

        main_layout = QVBoxLayout()
        self.main_image_label = QLabel(self)
        self.main_image_label.setAlignment(Qt.AlignCenter)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(100)

        self.scroll_widget = QWidget()
        self.thumbnail_layout = QHBoxLayout(self.scroll_widget)
        self.thumbnail_layout.setAlignment(Qt.AlignCenter)  # Center thumbnails
        self.scroll_area.setWidget(self.scroll_widget)

        main_layout.addWidget(self.main_image_label)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

        self.video_label = DraggableVideoLabel(self)
        self.video_label.move(20, 20)
        self.video_label.raise_()

        self.scroll_area.installEventFilter(self)
        self.change_image_requested.connect(self.handle_image_change)
        self.update_image()

    def handle_image_change(self, delta):
        self.current_index = (self.current_index + delta) % len(self.image_files)
        self.update_image()

    def update_image(self):
        if not self.image_files:
            return

        # Update main image
        main_pixmap = self.main_pixmaps[self.current_index].scaled(
            self.main_image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.main_image_label.setPixmap(main_pixmap)

        # Clear existing thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create new thumbnails
        for i in range(len(self.image_files)):
            thumb_label = QLabel(self)
            if i == self.current_index:
                thumb_label.setPixmap(self.selected_thumb_pixmaps[i])
                thumb_label.setStyleSheet("border: 2px solid blue; padding: 0px; margin: 0px;")
            else:
                thumb_label.setPixmap(self.unselected_thumb_pixmaps[i])
                thumb_label.setStyleSheet("padding: 0px; margin: 0px;")
            thumb_label.mousePressEvent = lambda event, idx=i: self.on_thumbnail_click(idx)
            self.thumbnail_layout.addWidget(thumb_label)

    def on_thumbnail_click(self, idx):
        self.current_index = idx
        self.update_image()

    def resizeEvent(self, event):
        # Resize the main image when the window is resized
        self.update_image()
        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.scroll_area and event.type() == QEvent.Wheel:
            delta = event.angleDelta().y()
            self.change_image_requested.emit(-1 if delta > 0 else 1)
            return True
        return super().eventFilter(obj, event)

    def start_gesture_recognition(self):
        self.gesture_thread = threading.Thread(target=self.gesture_control, daemon=True)
        self.gesture_thread.start()

    def gesture_control(self):
        cap = cv2.VideoCapture(0)
        hands = mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        prev_x = None
        last_swipe_time = 0
        cooldown = 0.5  # 500ms cooldown

        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                index_finger_x = hand_landmarks.landmark[8].x
                current_time = time.time()

                if prev_x is not None and (current_time - last_swipe_time) > cooldown:
                    delta_x = index_finger_x - prev_x
                    if delta_x > 0.05:
                        self.change_image_requested.emit(1)
                        last_swipe_time = current_time
                    elif delta_x < -0.05:
                        self.change_image_requested.emit(-1)
                        last_swipe_time = current_time

                prev_x = index_finger_x
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Update video feed
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.video_label.size(), Qt.KeepAspectRatio))

        cap.release()
        hands.close()

    def closeEvent(self, event):
        self.running = False
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    slider = ImageSlider()
    slider.show()
    sys.exit(app.exec_())