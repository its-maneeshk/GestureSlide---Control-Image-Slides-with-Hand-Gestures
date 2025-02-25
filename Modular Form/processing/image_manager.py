from PyQt5.QtGui import QPixmap
import os

class ImageManager:
    def __init__(self, image_folder="images"):
        self.image_folder = image_folder
        self.image_files = []
        self.current_index = 0
        self.main_pixmaps = []
        self.selected_thumb_pixmaps = []
        self.unselected_thumb_pixmaps = []
        self.load_images()

    def load_images(self):
        self.image_files = [os.path.join(self.image_folder, f) 
                          for f in sorted(os.listdir(self.image_folder))
                          if f.lower().endswith(("png", "jpg", "jpeg"))]
        self.preload_pixmaps()

    def preload_pixmaps(self):
        self.main_pixmaps = []
        self.selected_thumb_pixmaps = []
        self.unselected_thumb_pixmaps = []
        
        for img_path in self.image_files:
            main_pix = QPixmap(img_path)
            self.main_pixmaps.append(main_pix)
            
            self.selected_thumb_pixmaps.append(
                main_pix.scaled(100, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.unselected_thumb_pixmaps.append(
                main_pix.scaled(80, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def get_main_pixmap(self):
        return self.main_pixmaps[self.current_index].scaled(
            700, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def get_thumbnail_properties(self, index):
        if index == self.current_index:
            return self.selected_thumb_pixmaps[index], "border: 3px solid blue;"
        return self.unselected_thumb_pixmaps[index], ""