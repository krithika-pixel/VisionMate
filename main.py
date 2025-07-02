import cv2
import pyttsx3
import google.generativeai as genai
import numpy as np
import time
import threading
import speech_recognition as sr
from PIL import Image
import io

# Initialize TTS engine
engine = pyttsx3.init()

def speak(text):
    print("Speaking:", text)
    engine.say(text)
    engine.runAndWait()

# Initialize Gemini
genai.configure(api_key="AIzaSyC6scxscZwuTXCHOpIP_49zcNa5__yFAmE")
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# IP Webcam URL (replace with your phone's IP)
url = 'http://10.134.93.78:8080/video'  # Update IP
cap = cv2.VideoCapture(url)

status = "Press 's' or say 'scan' to scan surroundings..."
scan_triggered = False  # Flag for voice activation

def process_frame(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    response = model.generate_content([
        "Describe this scene briefly for a blind user. If there are any signs like STOP or traffic lights, mention them clearly.",
        pil_image
    ])
    description = response.text.strip()
    return description

# Voice recognition function
def listen_for_scan():
    global scan_triggered
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Microphone calibrated. Listening for 'scan'...")

    while True:
        with mic as source:
            try:
                print("Listening...")
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {command}")
                if "scan" in command:
                    print("Voice command 'scan' detected.")
                    scan_triggered = True
            except sr.WaitTimeoutError:
                print("Listening timed out, retrying...")
            except sr.UnknownValueError:
                print("Could not understand audio.")
            except sr.RequestError as e:
                print(f"Speech recognition service error: {e}")

# Start voice recognition in a separate thread
voice_thread = threading.Thread(target=listen_for_scan, daemon=True)
voice_thread.start()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera error.")
        continue

    cv2.putText(frame, status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.imshow("Blind Assist Tool", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s') or scan_triggered:
        scan_triggered = False  # reset flag
        status = "Analyzing surroundings..."
        speak("Analyzing surroundings")
        desc = process_frame(frame)
        speak(desc)

        # Detect important keywords
        if "stop sign" in desc.lower() or "stop" in desc.lower():
            speak("Stop! There's a stop sign.")
        elif "red light" in desc.lower():
            speak("Stop. It's a red light.")
        elif "yellow light" in desc.lower():
            speak("Caution. Yellow light ahead.")
        elif "green light" in desc.lower():
            speak("Green light. You can go.")

        status = "Press 's' or say 'scan' to scan surroundings..."

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()