import threading
from time import sleep
import tkinter as tk
from tkinter import ttk
from v10f import OCRDetector, ocr_results, ocr_results_lock

# Function to get the OCR result from the shared data
def get_ocr_result():
    with ocr_results_lock:
        return ocr_results

# Ensure the OCRDetector is initialized in a separate thread
def run_ocr_detector():
    OCRDetector()

ocr_thread = threading.Thread(target=run_ocr_detector)
ocr_thread.start()

# Allow some time for the detector to initialize and capture frames
sleep(5)

# Setup the main window using Tkinter
root = tk.Tk()
root.title("Detected Postcode Information")

ocr_label = ttk.Label(root, text="OCR: ", wraplength=300)
ocr_label.pack()

orientation_label = ttk.Label(root, text="Orientation: ", wraplength=300)
orientation_label.pack()

confidence_label = ttk.Label(root, text="Confidence: ", wraplength=300)
confidence_label.pack()

def update_labels():
    ocr_text, confidence, orientation = get_ocr_result()
    ocr_label.config(text=f"OCR: {ocr_text}")
    orientation_label.config(text=f"Orientation: {orientation}")
    confidence_label.config(text=f"Confidence: {confidence}%")
    root.after(1000, update_labels)  # Update labels every second

update_labels()
root.mainloop()
