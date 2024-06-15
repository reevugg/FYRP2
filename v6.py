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

# Function to read OCR with confidence score and detect orientation
def read_ocr(image):
    data = pytesseract.image_to_data(image, config='--psm 6', output_type=pytesseract.Output.DICT)
    for i in range(len(data['text'])):
        text = data['text'][i]
        conf = int(data['conf'][i])
        if re.match(r'\b\d{5}\b', text):
            print(f"Detected postcode: {text} with confidence {conf}%")
            return text, conf, detect_orientation(data)
    return "", 0, None

# Function to detect letters and infer image orientation
def detect_orientation(data):
    for text in data['text']:
        if re.search(r'[A-Za-z]', text):
            return 'upright'
    return 'upside-down'

# Function to rotate image and detect OCR
def detect_postcode_in_rotations(image):
    angles = [0, 90, 180, 270]
    for angle in angles:
        rotated_image = rotate_image(image, angle)
        if rotated_image is not None:
            ocr_text, conf, orientation = read_ocr(rotated_image)
            if ocr_text:
                print(f"Detected orientation: {orientation} at angle {angle} degrees")
                if orientation == 'upside-down':
                    continue
                return ocr_text, conf
    return "", 0

# Function to rotate image
def rotate_image(image, angle):
    if image is None:
        print(f"Received None image for rotation at angle {angle}")
        return None
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

# Function to process frame in a separate thread
def process_frame():
    global detected_ocr, confidence, frame, roi
    while True:
        if frame is not None:
            ocr_text, conf = detect_postcode_in_rotations(roi)
            if ocr_text:
                detected_ocr = ocr_text
                confidence = conf

# Function to display video frames and detect postcodes
def show_frame():
    global frame, start_time, detected_ocr, confidence, roi
    ret, frame = cap.read()

    if not ret or frame is None:
        print("Failed to grab frame")
        lmain.after(10, show_frame)
        return

    # Define the region of interest (ROI)
    height, width, _ = frame.shape
    roi_top = int(height * 0.3)
    roi_bottom = int(height * 0.7)
    roi_left = int(width * 0.3)
    roi_right = int(width * 0.7)
    roi = frame[roi_top:roi_bottom, roi_left:roi_right].copy()

    if roi is None or roi.size == 0:
        print("Failed to get a valid ROI")
        lmain.after(10, show_frame)
        return

    # Draw the bounding box for the scanning area
    cv2.rectangle(frame, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)

    end_time = time.time()
    fps = 1 / (end_time - start_time)
    fps_label.config(text=f"FPS: {fps:.2f}")

    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)

    ocr_label.config(text=f"OCR: {detected_ocr} (Confidence: {confidence}%)")

    start_time = time.time()
    lmain.after(10, show_frame)

# Initialize the video capture
cap = cv2.VideoCapture(0)
detected_ocr = ""
confidence = 0
frame = None
roi = None
start_time = time.time()

# Start a separate thread for frame processing
thread = threading.Thread(target=process_frame)
thread.daemon = True
thread.start()

# Setup the main window using Tkinter
root = tk.Tk()
root.title("Postcode Detection and OCR Reader")

lmain = tk.Label(root)
lmain.pack()

ocr_label = ttk.Label(root, text="OCR: ", wraplength=300)
ocr_label.pack()

fps_label = ttk.Label(root, text="FPS: ", wraplength=300)
fps_label.pack()

# Start displaying frames
show_frame()
root.mainloop()
