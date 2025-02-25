# GestureSlide - Image Slider Application

GestureSlide is an open-source application that allows you to browse images using hand gestures. It uses MediaPipe for hand tracking and PyQt5 for the user interface.

## Features
- Browse images in a folder using hand gestures.
- Dynamic image folder selection.
- Resizable main image view.
- Centered thumbnails for easy navigation.

## Installation

### Prerequisites
- Python 3.7 or higher
- PyQt5
- OpenCV
- MediaPipe

### Steps
1. Clone the repository:
   ```bash
pip install pyinstaller

Run PyInstaller to Create an Executable
Use this command to package everything into a single file (.exe):

powershell
Copy
Edit
pyinstaller --onefile --windowed --icon=icon.ico --name="GestureSlide" image_slider.py
🔹 Options Explained:

--onefile → Creates a single .exe file.
--windowed → Hides the console (useful for GUI apps).
--icon=icon.ico → Sets an icon for the .exe (optional).
--name="GestureSlide" → Sets the output .exe name.
