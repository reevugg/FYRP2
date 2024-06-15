import cv2
import pytesseract
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import re
import time
import threading

# Specify the full path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

# Function to read OCR (only 5 numerical digits) with confidence score
def read_ocr(image):
    data = pytesseract.image_to_data(image, config='--psm 6', output_type=pytesseract.Output.DICT)
    for i in range(len(data['text'])):
        text = data['text'][i]
        conf = int(data['conf'][i])
        if re.match(r'\b\d{5}\b', text):
            print(f"Detected postcode: {text} with confidence {conf}%")
            return text, conf
    return "", 0

# Function to process frame in a separate thread
def process_frame():
    global detected_ocr, confidence, frame
    while True:
        if frame is not None:
            ocr_text, conf = read_ocr(frame)
            if ocr_text:
                detected_ocr = ocr_text
                confidence = conf

# Function to display video frames and detect postcodes
def show_frame():
    global frame, start_time, detected_ocr, confidence
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        lmain.after(10, show_frame)
        return

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
