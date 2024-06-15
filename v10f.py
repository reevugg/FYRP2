import cv2
import pytesseract
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import re
import time
import threading
import numpy as np

# Specify the full path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

class OCRDetector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.detected_ocr = ""
            self.confidence = 0
            self.orientation = ""
            self.frame = None
            self.snapshot_interval = 300  # Interval in milliseconds (0.3 seconds)
            self.start_time = time.time()
            self.cap = cv2.VideoCapture(1)
            
            # Setup the main window using Tkinter
            self.root = tk.Tk()
            self.root.title("Postcode Detection and OCR Reader")
            self.lmain = tk.Label(self.root)
            self.lmain.pack()
            self.ocr_label = ttk.Label(self.root, text="OCR: ", wraplength=300)
            self.ocr_label.pack()
            self.orientation_label = ttk.Label(self.root, text="Orientation: ", wraplength=300)
            self.orientation_label.pack()
            self.fps_label = ttk.Label(self.root, text="FPS: ", wraplength=300)
            self.fps_label.pack()
            
            # Start capturing snapshots and displaying frames
            self.root.after(self.snapshot_interval, self.capture_snapshot)
            self.show_frame()
            self.root.mainloop()
            self.initialized = True

    def read_ocr(self, image):
        data = pytesseract.image_to_data(image, config='--psm 6', output_type=pytesseract.Output.DICT)
        for i in range(len(data['text'])):
            text = data['text'][i]
            conf = int(data['conf'][i])
            if re.match(r'\b\d{5}\b', text):
                print(f"Detected postcode: {text} with confidence {conf}%")
                return text, conf, self.detect_orientation(data)
        return "", 0, None

    def detect_orientation(self, data):
        for text in data['text']:
            if re.search(r'[A-Za-z]', text):
                return 'upright'
        return 'upside-down'

    def detect_postcode_in_rotations(self, image):
        angles = list(range(0, 360, 20))  # Angles at 20-degree intervals
        for angle in angles:
            rotated_image = self.rotate_image(image, angle)
            if rotated_image is not None:
                ocr_text, conf, orientation = self.read_ocr(rotated_image)
                if ocr_text:
                    print(f"Detected orientation: {orientation} at angle {angle} degrees")
                    if orientation == 'upside-down':
                        continue
                    self.orientation = orientation
                    return ocr_text, conf
        return "", 0

    def rotate_image(self, image, angle):
        if image is None:
            print(f"Received None image for rotation at angle {angle}")
            return None
        (h, w) = image.shape[:2]
        center = (w / 2, h / 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h))
        return rotated

    def process_frame(self, snapshot):
        ocr_text, conf = self.detect_postcode_in_rotations(snapshot)
        if ocr_text:
            self.detected_ocr = ocr_text
            self.confidence = conf
            global ocr_results
            with ocr_results_lock:
                ocr_results = (ocr_text, conf, self.orientation)

    def capture_snapshot(self):
        ret, self.frame = self.cap.read()
        if not ret or self.frame is None:
            print("Failed to grab frame")
            self.root.after(self.snapshot_interval, self.capture_snapshot)
            return

        # Define the region of interest (ROI)
        height, width, _ = self.frame.shape
        roi_top = int(height * 0.3)
        roi_bottom = int(height * 0.7)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        roi = self.frame[roi_top:roi_bottom, roi_left:roi_right].copy()

        if roi is None or roi.size == 0:
            print("Failed to get a valid ROI")
            self.root.after(self.snapshot_interval, self.capture_snapshot)
            return

        # Process the snapshot in a separate thread
        threading.Thread(target=self.process_frame, args=(roi,)).start()

        # Schedule the next snapshot
        self.root.after(self.snapshot_interval, self.capture_snapshot)

    def show_frame(self):
        if self.frame is not None:
            # Draw the bounding box for the scanning area
            height, width, _ = self.frame.shape
            roi_top = int(height * 0.3)
            roi_bottom = int(height * 0.7)
            roi_left = int(width * 0.3)
            roi_right = int(width * 0.7)
            cv2.rectangle(self.frame, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)

            end_time = time.time()
            time_diff = end_time - self.start_time
            fps = 1 / time_diff if time_diff > 0 else 0
            self.fps_label.config(text=f"FPS: {fps:.2f}")

            cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.lmain.imgtk = imgtk
            self.lmain.configure(image=imgtk)

            self.ocr_label.config(text=f"OCR: {self.detected_ocr} (Confidence: {self.confidence}%)")
            self.orientation_label.config(text=f"Orientation: {self.orientation}")

            self.start_time = time.time()
        self.lmain.after(10, self.show_frame)

    def get_ocr_result(self):
        global ocr_results
        with ocr_results_lock:
            return ocr_results

# Initialize the global variables for OCR results
ocr_results = ("", 0, "")
ocr_results_lock = threading.Lock()

def start_ocr_detector():
    detector = OCRDetector()
    return detector

if __name__ == "__main__":
    ocr_detector = start_ocr_detector()
