#!/usr/bin/env python3
"""
Smart Vision Bot - Main Application
A complete face recognition chatbot with real-time API integration
"""

import cv2
import time
import threading
import os
from datetime import datetime

from camera.stream import VideoStream
from camera.detect import FaceDetector
from recognizer.recognize import FaceRecognizer
from chatbot.llm_client import LLMClient
from chatbot.router import ChatRouter
from audio.tts import TTSEngine

class SmartVisionBot:
    def __init__(self):
        self.video_stream = None
        self.face_detector = FaceDetector()
        self.face_recognizer = FaceRecognizer()
        self.llm_client = LLMClient()
        self.chat_router = ChatRouter()
        self.tts_engine = TTSEngine()
        
        # State management
        self.identified = False
        self.current_person = None
        self.last_greeting_time = 0
        self.chat_history = []
        self.running = True
        
        # Threading
        self.chat_thread = None
        
    def initialize(self):
        """Initialize all components"""
        print("🤖 Initializing Smart Vision Bot...")
        
        # Load face encodings
        if not self.face_recognizer.load_encodings():
            print("❌ Failed to load face encodings. Run encode_faces.py first!")
            return False
            
        # Initialize video stream
        self.video_stream = VideoStream(src=0, width=640, height=480)
        time.sleep(2)  # Let camera warm up
        
        print("✅ Smart Vision Bot initialized successfully!")
        return True
        
    def detect_and_recognize(self, frame):
        """Detect and recognize faces in frame"""
        if self.identified:
            return None
            
        # Detect faces
        boxes = self.face_detector.detect(frame)
        if not boxes:
            return None
            
        # Recognize first detected face
        person_name = self.face_recognizer.identify(frame, boxes[0])
        return person_name
        
    def greet_person(self, person_name):
        """Greet the identified person"""
        current_time = time.time()
        
        # Prevent repeated greetings
        if current_time - self.last_greeting_time < 15:
            return
            
        greeting_time = datetime.now().strftime("%H:%M")
        
        if datetime.now().hour < 12:
            greeting = f"Good morning {person_name}! It's {greeting_time}. How can I help you today?"
        elif datetime.now().hour < 17:
            greeting = f"Good afternoon {person_name}! It's {greeting_time}. What can I do for you?"
        else:
            greeting = f"Good evening {person_name}! It's {greeting_time}. How may I assist you?"
            
        print(f"🤖: {greeting}")
        self.tts_engine.speak(greeting)
        
        self.last_greeting_time = current_time
        self.identified = True
        self.current_person = person_name
        
        # Initialize chat history with context
        self.chat_history = [
            {"role": "system", "content": f"You are a helpful AI assistant talking to {person_name}. Be friendly and conversational."}
        ]
        
    def start_chat_session(self):
        """Start interactive chat session"""
        print(f"\n💬 Chat session started with {self.current_person}")
        print("Type 'quit' or 'exit' to end the session")
        print("Type 'voice on/off' to toggle voice responses")
        print("-" * 50)
        
        voice_enabled = True
        
        while self.identified and self.running:
            try:
                user_input = input(f"\n{self.current_person}: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    farewell = f"Goodbye {self.current_person}! Have a great day!"
                    print(f"🤖: {farewell}")
                    if voice_enabled:
                        self.tts_engine.speak(farewell)
                    break
                    
                elif user_input.lower() == 'voice on':
                    voice_enabled = True
                    print("🤖: Voice responses enabled!")
                    continue
                    
                elif user_input.lower() == 'voice off':
                    voice_enabled = False
                    print("🤖: Voice responses disabled!")
                    continue
                    
                elif not user_input:
                    continue
                    
                # Process the query
                response = self.chat_router.process_query(user_input, self.chat_history, self.llm_client)
                print(f"🤖: {response}")
                
                if voice_enabled:
                    self.tts_engine.speak(response)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in chat: {e}")
                
        # Reset state
        self.identified = False
        self.current_person = None
        self.chat_history = []
        print("\n🔄 Chat session ended. Looking for faces again...")
        
    def run(self):
        """Main application loop"""
        if not self.initialize():
            return
            
        print("\n🎥 Camera started. Looking for faces...")
        print("Press 'q' to quit the application")
        
        try:
            while self.running:
                frame = self.video_stream.read()
                if frame is None:
                    continue
                    
                # Draw face detection boxes (for debugging)
                display_frame = frame.copy()
                boxes = self.face_detector.detect(frame)
                for (x, y, w, h) in boxes:
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                # Show status
                status_text = f"Status: {'Chatting with ' + self.current_person if self.identified else 'Looking for faces...'}"
                cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('Smart Vision Bot', display_frame)
                
                # Face recognition
                if not self.identified:
                    person_name = self.detect_and_recognize(frame)
                    if person_name:
                        self.greet_person(person_name)
                        # Start chat in separate thread
                        self.chat_thread = threading.Thread(target=self.start_chat_session, daemon=True)
                        self.chat_thread.start()
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        if self.video_stream:
            self.video_stream.stop()
            
        cv2.destroyAllWindows()
        self.tts_engine.cleanup()
        print("✅ Cleanup completed!")

if __name__ == "__main__":
    bot = SmartVisionBot()
    bot.run()