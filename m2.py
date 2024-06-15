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

# Global variables
detected_ocr = ""
confidence = 0
orientation = ""
detected_qr = ""
frame = None
snapshot_interval = 300  # Interval in milliseconds (0.3 seconds)
start_time = time.time()
mode = "OCR"  # Default mode is OCR

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
    angles = list(range(0, 360, 20))  # Angles at 20-degree intervals
    for angle in angles:
        rotated_image = rotate_image(image, angle)
        if rotated_image is not None:
            ocr_text, conf, orientation = read_ocr(rotated_image)
            if ocr_text:
                print(f"Detected orientation: {orientation} at angle {angle} degrees")
                if orientation == 'upside-down':
                    continue
                return ocr_text, conf, orientation
    return "", 0, ""

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

# Function to process frame for OCR in a separate thread
def process_frame_ocr(snapshot):
    global detected_ocr, confidence, orientation
    ocr_text, conf, orient = detect_postcode_in_rotations(snapshot)
    if ocr_text:
        detected_ocr = ocr_text
        confidence = conf
        orientation = orient

# Function to process frame for QR code in a separate thread
def process_frame_qr(snapshot):
    global detected_qr
    qr_detector = cv2.QRCodeDetector()
    data, bbox, _ = qr_detector.detectAndDecode(snapshot)
    if data:
        print(f"Detected QR code: {data}")
        detected_qr = data

# Function to capture and process snapshots
def capture_snapshot():
    global frame, snapshot_interval
    ret, frame = cap.read()

    if not ret or frame is None:
        print("Failed to grab frame")
        root.after(snapshot_interval, capture_snapshot)
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
        root.after(snapshot_interval, capture_snapshot)
        return

    # Process the snapshot in a separate thread
    if mode == "OCR":
        threading.Thread(target=process_frame_ocr, args=(roi,)).start()
    else:
        threading.Thread(target=process_frame_qr, args=(roi,)).start()

    # Schedule the next snapshot
    root.after(snapshot_interval, capture_snapshot)

# Function to display video frames
def show_frame():
    global frame, start_time, detected_ocr, confidence, detected_qr, orientation
    if frame is not None:
        # Draw the bounding box for the scanning area
        height, width, _ = frame.shape
        roi_top = int(height * 0.3)
        roi_bottom = int(height * 0.7)
        roi_left = int(width * 0.3)
        roi_right = int(width * 0.7)
        cv2.rectangle(frame, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 2)

        end_time = time.time()
        time_diff = end_time - start_time
        fps = 1 / time_diff if time_diff > 0 else 0
        fps_label.config(text=f"FPS: {fps:.2f}")

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)

        if mode == "OCR":
            ocr_label.config(text=f"OCR: {detected_ocr} (Confidence: {confidence}%) Orientation: {orientation}")
        else:
            qr_label.config(text=f"QR Code: {detected_qr}")

        start_time = time.time()
    lmain.after(10, show_frame)

# Function to switch to OCR mode
def switch_to_ocr():
    global mode
    mode = "OCR"
    qr_label.pack_forget()
    ocr_label.pack()
    start_capture()

# Function to switch to QR mode
def switch_to_qr():
    global mode
    mode = "QR"
    ocr_label.pack_forget()
    qr_label.pack()
    start_capture()

# Function to start capturing snapshots based on the mode
def start_capture():
    root.after(snapshot_interval, capture_snapshot)

# Initialize the video capture
cap = cv2.VideoCapture(1)

# Setup the main window using Tkinter
root = tk.Tk()
root.title("Postcode Detection and QR/OCR Reader")

# Mode selection buttons
btn_frame = tk.Frame(root)
btn_frame.pack()
ocr_button = ttk.Button(btn_frame, text="OCR Mode", command=switch_to_ocr)
ocr_button.pack(side=tk.LEFT)
qr_button = ttk.Button(btn_frame, text="QR Mode", command=switch_to_qr)
qr_button.pack(side=tk.LEFT)

lmain = tk.Label(root)
lmain.pack()

ocr_label = ttk.Label(root, text="OCR: ", wraplength=300)
qr_label = ttk.Label(root, text="QR Code: ", wraplength=300)

fps_label = ttk.Label(root, text="FPS: ", wraplength=300)
fps_label.pack()

# Start displaying frames
show_frame()

root.mainloop()
