import pyaudio
import wave
import threading
import speech_recognition as sr
import requests
import json
import bluetooth
import time
import websocket
import socket
import tkinter as tk
from googletrans import Translator

# إعدادات الصوت
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "output.wav"

def live_transcription():
    """التقاط الصوت وتحويله إلى نص في الوقت الفعلي"""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("بدء التعرف على الصوت...")
        while recording:
            try:
                audio = recognizer.listen(source, phrase_time_limit=2)
                text = recognizer.recognize_google(audio, language="ar")
                print(f"تم التعرف: {text}")
                translated_text = translate_text(text)
                send_to_led_display(translated_text)
                send_to_led_wifi(translated_text)
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                print("خطأ في الاتصال بخدمة التعرف على الصوت")
                break

def translate_text(text, target_language='en'):
    """ترجمة النص باستخدام Google Translate"""
    translator = Translator()
    translation = translator.translate(text, dest=target_language)
    return translation.text

def send_to_led_display(text):
    """إرسال النص إلى شاشة LED عبر WebSocket"""
    ws = websocket.WebSocket()
    ws.connect("ws://led-display.local:8080")
    ws.send(json.dumps({"text": text}))
    ws.close()

def send_to_led_wifi(text):
    """إرسال النص إلى شاشة LED عبر Wi-Fi باستخدام Sockets"""
    server_address = ('192.168.1.100', 5000)  # استبدل بعنوان اللوحة الفعلي
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(server_address)
        s.sendall(text.encode())

def bluetooth_server():
    """خادم Bluetooth للاستقبال من الريموت"""
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]
    
    bluetooth.advertise_service(server_sock, "TranslationRemote",
                                service_classes=[bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])
    
    print(f"Bluetooth server listening on port {port}...")
    client_sock, client_info = server_sock.accept()
    print(f"Accepted connection from {client_info}")
    
    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            command = data.decode()
            if command == "START_RECORD":
                global recording
                recording = True
                threading.Thread(target=live_transcription).start()
            elif command == "STOP_RECORD":
                recording = False
    finally:
        client_sock.close()
        server_sock.close()

# واجهة رسومية باستخدام Tkinter
def start_recording():
    global recording
    recording = True
    threading.Thread(target=live_transcription).start()

def stop_recording():
    global recording
    recording = False

root = tk.Tk()
root.title("نظام الترجمة الفورية")

start_button = tk.Button(root, text="ابدأ الترجمة الفورية", command=start_recording)
start_button.pack()

stop_button = tk.Button(root, text="إيقاف الترجمة", command=stop_recording)
stop_button.pack()

root.mainloop()

# بدء خادم Bluetooth
recording = False
threading.Thread(target=bluetooth_server).start()
