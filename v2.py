import cv2
import numpy as np
import pytesseract
from pyzbar import pyzbar
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import re
import time

# Specify the full path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

# Function to detect parcels in a given image
def detect_parcel(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

# Function to read OCR (only 5 numerical digits) with confidence score
def read_ocr(image):
    data = pytesseract.image_to_data(image, config='--psm 6', output_type=pytesseract.Output.DICT)
    for i in range(len(data['text'])):
        text = data['text'][i]
        conf = int(data['conf'][i])
        if re.match(r'\b\d{5}\b', text):
            return text, conf
    return "", 0

# Function to display video frames and detect parcels
def show_frame():
    start_time = time.time()
    _, frame = cap.read()
    
    # Define the region of interest (ROI)
    height, width, _ = frame.shape
    roi_top = int(height * 0.3)
    roi_bottom = int(height * 0.7)
    roi_left = int(width * 0.3)
    roi_right = int(width * 0.7)
    roi = frame[roi_top:roi_bottom, roi_left:roi_right]

    contours = detect_parcel(roi)
    detected_ocr = ""
    confidence = 0

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 2)
        parcel = roi[y:y+h, x:x+w]
        ocr_text, conf = read_ocr(parcel)
        if ocr_text:
            detected_ocr = ocr_text
            confidence = conf
            break

    ocr_label.config(text=f"OCR: {detected_ocr} (Confidence: {confidence}%)")
    
    end_time = time.time()
    fps = 1 / (end_time - start_time)
    fps_label.config(text=f"FPS: {fps:.2f}")

    # Display the ROI on the original frame
    frame[roi_top:roi_bottom, roi_left:roi_right] = roi
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)

    lmain.after(10, show_frame)

# Initialize the video capture
cap = cv2.VideoCapture(0)

# Setup the main window using Tkinter
root = tk.Tk()
root.title("Parcel Detection and OCR Reader")

lmain = tk.Label(root)
lmain.pack()

ocr_label = ttk.Label(root, text="OCR: ", wraplength=300)
ocr_label.pack()

fps_label = ttk.Label(root, text="FPS: ", wraplength=300)
fps_label.pack()

# Start displaying frames
show_frame()
root.mainloop()
