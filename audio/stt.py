# stt.py
"""
Speech-to-Text helper for Smart Vision Bot
Uses speech_recognition with microphone input
"""

import speech_recognition as sr

recognizer = sr.Recognizer()
microphone = sr.Microphone()

def listen_once() -> str:
    """Capture one phrase from the mic and return as text"""
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

        text = recognizer.recognize_google(audio)
        print(f"🗣 Recognized: {text}")
        return text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return f"⚠️ Speech recognition error: {e}"
