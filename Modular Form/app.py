import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPixmap
from gui.components import ImageSlider, DraggableVideoLabel
from processing.gesture_controller import GestureController
from processing.image_manager import ImageManager

class GestureSlideApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.image_manager = ImageManager()
        self.slider = ImageSlider(self.image_manager)
        self.gesture_controller = GestureController()
        self.setup_connections()
        self.start_gesture_processing()

    def setup_connections(self):
        self.gesture_controller.gesture_detected.connect(self.slider.change_image_requested)
        self.gesture_controller.frame_processed.connect(self.update_video_feed)
        self.slider.destroyed.connect(self.gesture_controller.stop)

    def start_gesture_processing(self):
        import threading
        self.thread = threading.Thread(target=self.gesture_controller.start_capture, daemon=True)
        self.thread.start()

    def update_video_feed(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.slider.video_label.setPixmap(
            QPixmap.fromImage(q_img).scaled(
                self.slider.video_label.size(), Qt.KeepAspectRatio))

    def run(self):
        self.slider.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = GestureSlideApp()
    app.run()