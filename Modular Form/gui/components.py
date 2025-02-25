from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, 
                            QWidget, QScrollArea, QFrame)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QEvent, QPoint, pyqtSignal

class DraggableVideoLabel(QLabel):
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
    
    def __init__(self, image_manager):
        super().__init__()
        self.image_manager = image_manager
        self.initUI()
        self.setup_connections()

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
        self.scroll_area.setWidget(self.scroll_widget)

        main_layout.addWidget(self.main_image_label)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

        self.video_label = DraggableVideoLabel(self)
        self.video_label.move(20, 20)
        self.video_label.raise_()

        self.scroll_area.installEventFilter(self)
        self.update_image()

    def setup_connections(self):
        self.change_image_requested.connect(self.handle_image_change)

    def handle_image_change(self, delta):
        self.image_manager.current_index = (
            self.image_manager.current_index + delta) % len(self.image_manager.image_files)
        self.update_image()

    def update_image(self):
        if not self.image_manager.image_files:
            return

        self.main_image_label.setPixmap(self.image_manager.get_main_pixmap())
        self.update_thumbnails()

    def update_thumbnails(self):
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i in range(len(self.image_manager.image_files)):
            thumb_label = QLabel(self)
            pixmap, style = self.image_manager.get_thumbnail_properties(i)
            thumb_label.setPixmap(pixmap)
            thumb_label.setStyleSheet(style)
            thumb_label.mousePressEvent = lambda event, idx=i: self.on_thumbnail_click(idx)
            self.thumbnail_layout.addWidget(thumb_label)

    def on_thumbnail_click(self, idx):
        self.image_manager.current_index = idx
        self.update_image()

    def eventFilter(self, obj, event):
        if obj == self.scroll_area and event.type() == QEvent.Wheel:
            delta = event.angleDelta().y()
            self.change_image_requested.emit(-1 if delta > 0 else 1)
            return True
        return super().eventFilter(obj, event)