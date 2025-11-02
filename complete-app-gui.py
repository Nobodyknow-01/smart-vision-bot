# complete-app-gui.py
import customtkinter as ctk
from tkinter import messagebox
import cv2
import threading
import time
import os
import pickle
import face_recognition
from PIL import Image, ImageTk
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
import pyttsx3
import sys
import requests
import urllib.parse
from audio.stt import listen_once



# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Global request headers to avoid simple 403s (Wikipedia and other APIs often block default agents)
REQUEST_HEADERS = {
    "User-Agent": "SmartVisionBot/1.0 (https://example.com) PythonClient/1.0",
    "Accept": "application/json",
}

class TypingIndicator:
    """Animated typing indicator for chat"""
    def __init__(self, parent):
        self.parent = parent
        self.typing_frame = None
        self.animation_running = False
        
    def start(self):
        """Start typing animation"""
        if self.animation_running:
            return
            
        self.animation_running = True
        
        # Create typing indicator frame
        self.typing_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.typing_frame.pack(fill="x", padx=20, pady=(10, 5), anchor="w")
        
        # Bot message container
        bot_container = ctk.CTkFrame(self.typing_frame, fg_color="transparent")
        bot_container.pack(anchor="w")
        
        # Modern avatar frame
        avatar_frame = ctk.CTkFrame(bot_container, width=40, height=40, corner_radius=20, 
                                   fg_color="#4F46E5")
        avatar_frame.pack(side="left", padx=(0, 12))
        avatar_frame.pack_propagate(False)
        
        # Avatar icon
        avatar_label = ctk.CTkLabel(avatar_frame, text="AI", 
                                   font=ctk.CTkFont("SF Pro Display", 12, "bold"),
                                   text_color="white")
        avatar_label.pack(expand=True)
        
        # Typing bubble
        typing_bubble = ctk.CTkFrame(bot_container, fg_color="#2D3748", corner_radius=18)
        typing_bubble.pack(side="left")
        
        self.typing_label = ctk.CTkLabel(typing_bubble, text="AI is thinking", 
                                        font=ctk.CTkFont("SF Pro Display", 11),
                                        text_color="#A0ADB8")
        self.typing_label.pack(padx=16, pady=12)
        
        # Start animation
        threading.Thread(target=self.animate, daemon=True).start()
    
    def animate(self):
        """Animate the dots"""
        dots = ["", ".", "..", "..."]
        i = 0
        while self.animation_running:
            try:
                if self.typing_label and self.typing_label.winfo_exists():
                    self.typing_label.configure(text=f"AI is thinking{dots[i % len(dots)]}")
                    i += 1
                    time.sleep(0.5)
                else:
                    break
            except:
                break
    
    def stop(self):
        """Stop typing animation"""
        self.animation_running = False
        if self.typing_frame and self.typing_frame.winfo_exists():
            self.typing_frame.destroy()

class SmartVisionBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Vision Bot")
        self.root.geometry("1500x950")
        
        # Theme state
        self.current_theme = "dark"
        
        # Modern color palette
        self.colors = {
            'primary': '#1A202C',
            'secondary': '#2D3748', 
            'accent': '#4F46E5',
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'user_bubble': '#4F46E5',
            'bot_bubble': '#374151',
            'text_primary': '#FFFFFF',
            'text_secondary': '#A0ADB8',
            'border': '#4A5568'
        }
        
        # Initialize variables
        self.cap = None
        self.camera_running = False
        self.identified = False
        self.person_name = ""
        self.face_encodings = []
        self.face_names = []
        self.voice_enabled = False
        self.tts_engine = None
        self.chat_history = []
        self.typing_indicator = None
        
        # System status tracking
        self.system_status = {
            'env_loaded': False,
            'apis_loaded': False,
            'chatbot_modules': False,
            'face_encodings': False,
            'tts_ready': False,
            'camera_ready': False
        }
        
        # Load everything with confirmation
        self.initialize_system()
        
        # Setup modern GUI
        self.setup_gui()
        
        # Initialize camera
        self.init_camera()
    
    def log_status(self, message, success=True):
        """Log system status messages (only to terminal)"""
        status = "✓" if success else "❌"
        print(f"{status} {message}")

    # [Keep all initialization methods the same as before]
    def initialize_system(self):
        """Initialize all system components with confirmation messages"""
        print("=" * 60)
        print("🚀 SMART VISION BOT INITIALIZATION")
        print("=" * 60)
        
        # 1. Load environment variables
        self.load_environment_variables()
        
        # 2. Load chatbot modules
        self.load_chatbot_modules()
        
        # 3. Initialize TTS
        self.init_tts()
        
        # 4. Load face encodings
        self.load_face_encodings()
        
        # 5. Validate APIs
        self.validate_apis()
        
        # 6. Print final status
        self.print_system_status()
    
    def load_environment_variables(self):
        """Load and validate environment variables"""
        try:
            # Try multiple methods to load .env
            loaded = False
            
            if load_dotenv(find_dotenv()):
                loaded = True
                self.log_status("Environment variables loaded using find_dotenv()")
            elif load_dotenv('.env'):
                loaded = True
                self.log_status("Environment variables loaded from .env")
            elif os.path.exists('.env'):
                load_dotenv('.env', override=True)
                loaded = True
                self.log_status("Environment variables loaded with override")
            
            if not loaded:
                self.log_status("No .env file found, using system environment", False)
            
            # Check for required API keys
            self.groq_api_key = os.getenv('GROQ_API_KEY')
            self.gnews_api_key = os.getenv('GNEWS_API_KEY')
            
            # Log API key status
            if self.groq_api_key:
                self.log_status(f"Groq API Key: Found ({len(self.groq_api_key[:10])}...)")
            else:
                self.log_status("Groq API Key: Missing", False)
            
            if self.gnews_api_key:
                self.log_status(f"GNews API Key: Found ({len(self.gnews_api_key[:10])}...)")
            else:
                self.log_status("GNews API Key: Missing", False)
            
            self.system_status['env_loaded'] = True
            
        except Exception as e:
            self.log_status(f"Error loading environment: {e}", False)
    
    def load_chatbot_modules(self):
        """Load and validate chatbot modules"""
        try:
            # Check if chatbot directory exists
            chatbot_dir = os.path.join(os.path.dirname(__file__), 'chatbot')
            if not os.path.exists(chatbot_dir):
                self.log_status("Chatbot directory not found", False)
                return
            
            # Try importing each module
            modules_to_load = ['router', 'weather', 'news', 'finance', 'facts', 'llm_client', 'ticker_map']
            loaded_modules = []
            
            for module in modules_to_load:
                try:
                    exec(f"from chatbot import {module}")
                    loaded_modules.append(module)
                    self.log_status(f"Loaded chatbot.{module}")
                except ImportError as e:
                    self.log_status(f"Failed to load chatbot.{module}: {e}", False)
            
            if len(loaded_modules) == len(modules_to_load):
                # Import the main router
                from chatbot import router
                self.router = router
                self.system_status['chatbot_modules'] = True
                self.log_status(f"All {len(loaded_modules)} chatbot modules loaded successfully")
            else:
                self.log_status(f"Only {len(loaded_modules)}/{len(modules_to_load)} modules loaded", False)
                # Fallback to basic responses
                self.router = None
                
        except Exception as e:
            self.log_status(f"Error loading chatbot modules: {e}", False)
            self.router = None
    
    def init_tts(self):
        """Initialize text-to-speech with confirmation"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
            
            # Test TTS
            voices = self.tts_engine.getProperty('voices')
            voice_count = len(voices) if voices else 0
            
            self.log_status(f"TTS Engine initialized with {voice_count} voices")
            self.system_status['tts_ready'] = True
            
        except Exception as e:
            self.log_status(f"TTS initialization failed: {e}", False)
            self.tts_engine = None
    
    def load_face_encodings(self):
        """Load face encodings with detailed status"""
        try:
            encoding_file = 'encodings.pkl'
            if os.path.exists(encoding_file):
                with open(encoding_file, 'rb') as f:
                    data = pickle.load(f)
                    self.face_encodings = data['encodings']
                    self.face_names = data['names']
                
                self.log_status(f"Face encodings loaded: {len(self.face_names)} identities")
                for name in self.face_names:
                    self.log_status(f"  - {name}")
                
                self.system_status['face_encodings'] = True
            else:
                self.log_status(f"Face encoding file '{encoding_file}' not found", False)
                self.log_status("Face recognition will be disabled")
                
        except Exception as e:
            self.log_status(f"Error loading face encodings: {e}", False)
    
    def validate_apis(self):
        """Validate API connections with improved DuckDuckGo handling"""
        self.log_status("Validating API connections...")
        
        # Test basic connectivity
        import requests
        
        # Test DuckDuckGo with rate limit awareness (include headers)
        try:
            time.sleep(1)  # Small delay before test
            resp = requests.get("https://api.duckduckgo.com/?q=test&format=json&no_html=1", headers=REQUEST_HEADERS, timeout=8)
            if resp.status_code == 200:
                self.log_status("DuckDuckGo API: Connected")
            elif resp.status_code == 202:
                self.log_status("DuckDuckGo API: Rate limited (normal behavior)")
            else:
                self.log_status(f"DuckDuckGo API: Status {resp.status_code}")
        except Exception as e:
            self.log_status(f"DuckDuckGo API: Connection test failed - {e}", False)
        
        # Test Open-Meteo (no key required)
        try:
            time.sleep(0.5)
            resp = requests.get("https://api.open-meteo.com/v1/forecast?latitude=28.6139&longitude=77.2090&current_weather=true", headers=REQUEST_HEADERS, timeout=5)
            if resp.status_code == 200:
                self.log_status("Open-Meteo Weather API: Connected")
            else:
                self.log_status(f"Open-Meteo API: Error {resp.status_code}", False)
        except Exception as e:
            self.log_status(f"Open-Meteo API: Connection failed - {e}", False)
        
        # Test Wikipedia with User-Agent header to avoid 403
        try:
            time.sleep(0.5)
            resp = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/Python", headers=REQUEST_HEADERS, timeout=5)
            if resp.status_code == 200:
                self.log_status("Wikipedia API: Connected")
            else:
                self.log_status(f"Wikipedia API: Error {resp.status_code}", False)
        except Exception as e:
            self.log_status(f"Wikipedia API: Connection failed - {e}", False)
        
        # Test GNews (if key available)
        if self.gnews_api_key:
            try:
                time.sleep(0.5)
                resp = requests.get(f"https://gnews.io/api/v4/search?q=test&token={self.gnews_api_key}&max=1", headers=REQUEST_HEADERS, timeout=8)
                if resp.status_code == 200:
                    self.log_status("GNews API: Connected and authenticated")
                elif resp.status_code == 429:
                    self.log_status("GNews API: Rate limited")
                else:
                    self.log_status(f"GNews API: Error {resp.status_code}", False)
            except Exception as e:
                self.log_status(f"GNews API: Connection failed - {e}", False)
        
        # Test Groq (if key available)
        if self.groq_api_key:
            try:
                time.sleep(0.5)
                headers = {'Authorization': f'Bearer {self.groq_api_key}', **REQUEST_HEADERS}
                resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=8)
                if resp.status_code == 200:
                    self.log_status("Groq API: Connected and authenticated")
                else:
                    self.log_status(f"Groq API: Error {resp.status_code}", False)
            except Exception as e:
                self.log_status(f"Groq API: Connection failed - {e}", False)
        
        self.system_status['apis_loaded'] = True
    
    def print_system_status(self):
        """Print final system status summary"""
        print("\n" + "=" * 60)
        print("📊 SYSTEM STATUS SUMMARY")
        print("=" * 60)
        
        for component, status in self.system_status.items():
            status_icon = "✅" if status else "❌"
            component_name = component.replace('_', ' ').title()
            print(f"{status_icon} {component_name}: {'Ready' if status else 'Failed'}")
        
        ready_count = sum(self.system_status.values())
        total_count = len(self.system_status)
        
        print(f"\n🎯 Overall Status: {ready_count}/{total_count} components ready")
        
        if ready_count == total_count:
            print("🚀 System fully operational!")
        else:
            print("⚠️  Some components failed - functionality may be limited")
        
        print("=" * 60 + "\n")
    
    def setup_gui(self):
        """Setup ultra-modern GUI with premium styling"""
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color="#0F1419", corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Header frame
        self.create_premium_header(main_frame)
        
        # Content frame (split layout)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left panel - Camera with premium neon border
        self.create_premium_camera_panel(content_frame)
        
        # Right panel - Premium chat interface
        self.create_premium_chat_panel(content_frame)
        
        self.log_status("Premium GUI setup completed")
    
    def create_premium_header(self, parent):
        """Create premium header with glassmorphic effect"""
        header_frame = ctk.CTkFrame(parent, height=80, corner_radius=0, 
                                   fg_color="#1A202C", border_width=1, border_color="#2D3748")
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Center the entire header content
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both")
        
        # Left section - Title and status (centered)
        title_section = ctk.CTkFrame(header_content, fg_color="transparent")
        title_section.pack(expand=True, side="left", fill="both")
        
        # Center container for title and status
        center_container = ctk.CTkFrame(title_section, fg_color="transparent")
        center_container.pack(expand=True)
        
        # Main title
        title_label = ctk.CTkLabel(center_container, text="Smart Vision Bot", 
                                  font=ctk.CTkFont("SF Pro Display", 28, "bold"),
                                  text_color="#FFFFFF")
        title_label.pack(pady=(20, 5))
        
        # Status container
        status_container = ctk.CTkFrame(center_container, fg_color="transparent")
        status_container.pack()
        
        # Status indicator
        self.status_dot = ctk.CTkLabel(status_container, text="●", 
                                     font=ctk.CTkFont(size=14), text_color="#10B981")
        self.status_dot.pack(side="left")
        
        status_label = ctk.CTkLabel(status_container, text="Connected", 
                                   font=ctk.CTkFont("SF Pro Display", 13),
                                   text_color="#10B981")
        status_label.pack(side="left", padx=(5, 0))
        
        # Right section - Premium control buttons
        controls_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        controls_frame.pack(side="right", padx=30, pady=20)
        
        # Store button references for theme switching
        self.theme_buttons = {}
        
        # Create premium buttons
        self.theme_buttons['reset'] = self.create_premium_button(
    controls_frame, 
    "Reset", 
    self.reset_system
)

        self.theme_buttons['voice'] = self.create_premium_button(controls_frame, "🔊 Voice ON", 
                                                               self.toggle_voice, 
                                                               color=self.colors['success'])
        self.theme_buttons['light'] = self.create_premium_button(controls_frame, "Light", 
                                                               lambda: self.switch_theme("light"))
        self.theme_buttons['dark'] = self.create_premium_button(controls_frame, "Dark", 
                                                              lambda: self.switch_theme("dark"), 
                                                              is_active=True)
    

    def reset_system(self):
        """Reset face recognition and chat history"""
        self.identified = False
        self.person_name = ""
        self.chat_history.clear()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.add_premium_chat_message("System", "🔄 System reset. Please look at the camera for recognition.", is_user=False)
        self.message_entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        if hasattr(self, "mic_btn"):
            self.mic_btn.configure(state="disabled")
        self.log_status("System reset performed")

    def create_premium_button(self, parent, text, command, is_active=False, color=None):
        """Create premium styled button with animations"""
        if color is None:
            color = self.colors['accent'] if is_active else "#374151"
        
        btn = ctk.CTkButton(
            parent, 
            text=text, 
            command=command,
            width=100, 
            height=36,
            font=ctk.CTkFont("SF Pro Display", 12, "bold"),
            fg_color=color,
            hover_color=self.colors['accent'] if not is_active else "#6366F1",
            corner_radius=18,
            border_width=2,
            border_color="#4A5568" if not is_active else color
        )
        btn.pack(side="right", padx=8)
        return btn
    
    def create_premium_camera_panel(self, parent):
        """Create premium camera panel with advanced neon effects"""
        # Camera container with premium styling
        camera_container = ctk.CTkFrame(parent, corner_radius=20, fg_color="#1A202C",
                                       border_width=2, border_color="#2D3748")
        camera_container.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Camera display with advanced neon border
        camera_display_frame = ctk.CTkFrame(camera_container, corner_radius=16, 
                                          border_width=3, border_color="#4F46E5",
                                          fg_color="#000000")
        camera_display_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Camera label for video feed
        self.camera_label = ctk.CTkLabel(camera_display_frame, text="Camera Initializing...",
                                        font=ctk.CTkFont("SF Pro Display", 18, "bold"),
                                        text_color="#A0ADB8")
        self.camera_label.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Premium camera controls
        controls_frame = ctk.CTkFrame(camera_container, fg_color="transparent", height=70)
        controls_frame.pack(fill="x", padx=20, pady=(0, 20))
        controls_frame.pack_propagate(False)
        
        # Camera button with premium styling
        self.camera_btn = ctk.CTkButton(
            controls_frame, 
            text="⏹ Stop Camera", 
            command=self.toggle_camera,
            width=140, 
            height=44,
            font=ctk.CTkFont("SF Pro Display", 13, "bold"),
            fg_color=self.colors['error'],
            hover_color="#DC2626",
            corner_radius=22
        )
        self.camera_btn.pack(side="left", pady=13)
        
        # Camera status with premium styling
        self.camera_status = ctk.CTkLabel(
            controls_frame, 
            text="Camera Running",
            font=ctk.CTkFont("SF Pro Display", 13, "bold"),
            text_color=self.colors['success']
        )
        self.camera_status.pack(side="right", pady=15, padx=15)
    
    def create_premium_chat_panel(self, parent):
        """Create premium chat interface with modern message bubbles"""
        # Chat container with premium styling
        chat_container = ctk.CTkFrame(parent, corner_radius=20, fg_color="#1A202C",
                                     border_width=2, border_color="#2D3748")
        chat_container.pack(side="right", fill="both", expand=True)
        
        # Chat header
        chat_header = ctk.CTkFrame(chat_container, height=60, corner_radius=16,
                                  fg_color="#2D3748")
        chat_header.pack(fill="x", padx=20, pady=(20, 10))
        chat_header.pack_propagate(False)
        
        header_label = ctk.CTkLabel(chat_header, text="Chat Interface", 
                                   font=ctk.CTkFont("SF Pro Display", 18, "bold"),
                                   text_color="#FFFFFF")
        header_label.pack(pady=18)
        
        # Scrollable chat area with premium styling
        self.chat_frame = ctk.CTkScrollableFrame(
            chat_container, 
            corner_radius=16,
            fg_color="#0F1419",
            scrollbar_button_color="#4A5568",
            scrollbar_button_hover_color="#6B7280"
        )
        self.chat_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Initialize typing indicator
        self.typing_indicator = TypingIndicator(self.chat_frame)
        
        # Premium chat input frame
        input_frame = ctk.CTkFrame(chat_container, fg_color="transparent", height=80)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))
        input_frame.pack_propagate(False)
        
        # Premium message input
        self.message_entry = ctk.CTkEntry(
            input_frame, 
            placeholder_text="Type your message...",
            height=50,
            font=ctk.CTkFont("SF Pro Display", 13),
            corner_radius=25,
            border_width=2,
            border_color="#374151",
            fg_color="#2D3748",
            placeholder_text_color="#6B7280"
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=15)
        self.message_entry.bind("<Return>", self.send_message)
        
                # Premium mic button
        self.mic_btn = ctk.CTkButton(
            input_frame, 
            text="🎤 Start Mic", 
            command=self.toggle_mic,
            width=120, 
            height=50,
            font=ctk.CTkFont("SF Pro Display", 13, "bold"),
            fg_color=self.colors['success'],
            hover_color="#059669",
            corner_radius=25
        )
        self.mic_btn.pack(side="right", padx=(0, 10), pady=15)

        # Premium send button
        self.send_btn = ctk.CTkButton(
            input_frame, 
            text="➤ Send", 
            command=self.send_message,
            width=100, 
            height=50,
            font=ctk.CTkFont("SF Pro Display", 13, "bold"),
            fg_color=self.colors['accent'],
            hover_color="#6366F1",
            corner_radius=25
        )
        self.send_btn.pack(side="right", pady=15)
        
        # Initially disable chat until face recognition
        self.message_entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")

    def toggle_mic(self):
        """Toggle mic listening"""
        if hasattr(self, "mic_active") and self.mic_active:
            self.mic_active = False
            self.mic_btn.configure(text="🎤 Start Mic", fg_color=self.colors['success'])
            self.log_status("Mic stopped")
        else:
            self.mic_active = True
            self.mic_btn.configure(text="⏹ Stop Mic", fg_color=self.colors['error'])
            self.log_status("Mic started")
            threading.Thread(target=self.listen_and_send, daemon=True).start()

    def listen_and_send(self):
        """Listen via mic and send as message"""
        while getattr(self, "mic_active", False):
            text = listen_once()
            if text:
                self.root.after(0, lambda: self.insert_mic_message(text))
            else:
                self.log_status("No speech detected")
            self.toggle_mic()  # Auto-stop after one recognition (push-to-talk)
            break

    def insert_mic_message(self, text: str):
        """Insert mic recognized text into entry and send"""
        self.message_entry.delete(0, "end")
        self.message_entry.insert(0, text)
        self.send_message()

    
    def add_premium_chat_message(self, sender, message, is_user=False):
        """Add premium message with FIXED text wrapping to prevent cutoff"""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Message container with proper spacing
        msg_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_container.pack(fill="x", padx=5, pady=15)
        
        if is_user:
            # User message (right side, premium blue)
            user_container = ctk.CTkFrame(msg_container, fg_color="transparent")
            user_container.pack(anchor="e", fill="x")
            
            # Content frame with flexible width
            content_frame = ctk.CTkFrame(user_container, fg_color="transparent")
            content_frame.pack(anchor="e", padx=(80, 10))
            
            # User avatar
            avatar_frame = ctk.CTkFrame(content_frame, width=36, height=36, corner_radius=18, 
                                       fg_color="#FFFFFF")
            avatar_frame.pack(side="right", padx=(12, 0), pady=(0, 5))
            avatar_frame.pack_propagate(False)
            
            avatar_label = ctk.CTkLabel(avatar_frame, text="U", 
                                       font=ctk.CTkFont("SF Pro Display", 14, "bold"),
                                       text_color=self.colors['user_bubble'])
            avatar_label.pack(expand=True)
            
            # Message bubble with AUTO-SIZING
            message_frame = ctk.CTkFrame(content_frame, fg_color=self.colors['user_bubble'], 
                                       corner_radius=20, border_width=1, border_color="#6366F1")
            message_frame.pack(side="right", padx=(0, 12), pady=(0, 5))
            
            # Message content
            msg_content_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
            msg_content_frame.pack(padx=15, pady=12)
            
            # Timestamp
            time_label = ctk.CTkLabel(msg_content_frame, text=timestamp, 
                                     font=ctk.CTkFont("SF Pro Display", 10),
                                     text_color="#B8BCC8")
            time_label.pack(anchor="e", pady=(0, 4))
            
            # Message text with FIXED wrapping
            msg_label = ctk.CTkLabel(msg_content_frame, text=message, 
                                    font=ctk.CTkFont("SF Pro Display", 12),
                                    text_color="#FFFFFF",
                                    wraplength=280,  # Reduced wrap length
                                    justify="right",
                                    anchor="e")
            msg_label.pack(anchor="e")
            
        else:
            # Bot message (left side, premium dark)
            bot_container = ctk.CTkFrame(msg_container, fg_color="transparent")
            bot_container.pack(anchor="w", fill="x")
            
            # Content frame with flexible width
            content_frame = ctk.CTkFrame(bot_container, fg_color="transparent")
            content_frame.pack(anchor="w", padx=(10, 80))
            
            # Bot avatar
            avatar_frame = ctk.CTkFrame(content_frame, width=36, height=36, corner_radius=18, 
                                       fg_color=self.colors['accent'])
            avatar_frame.pack(side="left", padx=(0, 12), pady=(0, 5))
            avatar_frame.pack_propagate(False)
            
            avatar_label = ctk.CTkLabel(avatar_frame, text="AI", 
                                       font=ctk.CTkFont("SF Pro Display", 12, "bold"),
                                       text_color="#FFFFFF")
            avatar_label.pack(expand=True)
            
            # Message bubble with AUTO-SIZING
            message_frame = ctk.CTkFrame(content_frame, fg_color=self.colors['bot_bubble'], 
                                       corner_radius=20, border_width=1, border_color="#4A5568")
            message_frame.pack(side="left", padx=(12, 0), pady=(0, 5))
            
            # Message content
            msg_content_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
            msg_content_frame.pack(padx=15, pady=12)
            
            # Timestamp
            time_label = ctk.CTkLabel(msg_content_frame, text=timestamp, 
                                     font=ctk.CTkFont("SF Pro Display", 10),
                                     text_color="#6B7280")
            time_label.pack(anchor="w", pady=(0, 4))
            
            # Message text with FIXED wrapping
            msg_label = ctk.CTkLabel(msg_content_frame, text=message, 
                                    font=ctk.CTkFont("SF Pro Display", 12),
                                    text_color="#FFFFFF",
                                    wraplength=320,  # Proper wrap length for bot messages
                                    justify="left",
                                    anchor="w")
            msg_label.pack(anchor="w")
        
        # Auto-scroll to bottom
        try:
            # CTkScrollableFrame holds a _parent_canvas attr internally; this is a best-effort scroll to bottom
            self.chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
    
    def switch_theme(self, theme):
        """FIXED theme switching functionality"""
        self.current_theme = theme
        ctk.set_appearance_mode(theme)
        
        # Update button appearances
        if theme == "dark":
            self.theme_buttons['dark'].configure(fg_color=self.colors['accent'], 
                                               border_color=self.colors['accent'])
            self.theme_buttons['light'].configure(fg_color="#374151", 
                                                border_color="#4A5568")
        else:
            self.theme_buttons['light'].configure(fg_color=self.colors['accent'], 
                                                border_color=self.colors['accent'])
            self.theme_buttons['dark'].configure(fg_color="#374151", 
                                               border_color="#4A5568")
        
        self.log_status(f"Theme switched to {theme} mode")
    
    def toggle_voice(self):
        """Toggle voice output with premium button styling"""
        self.voice_enabled = not self.voice_enabled
        if self.voice_enabled:
            self.theme_buttons['voice'].configure(text="🔊 Voice ON", 
                                                fg_color=self.colors['success'])
        else:
            self.theme_buttons['voice'].configure(text="🔇 Voice OFF", 
                                                fg_color=self.colors['error'])
        self.log_status(f"Voice {'enabled' if self.voice_enabled else 'disabled'}")
    
    # [Keep all camera and processing methods the same as before]
    def init_camera(self):
        """Initialize camera"""
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.log_status(f"Camera initialized successfully ({frame.shape[1]}x{frame.shape})")
                    self.system_status['camera_ready'] = True
                    self.toggle_camera()
                else:
                    self.log_status("Camera opened but cannot read frames", False)
            else:
                self.log_status("Failed to open camera", False)
        except Exception as e:
            self.log_status(f"Camera initialization error: {e}", False)
    
    def toggle_camera(self):
        """Toggle camera on/off"""
        if not self.camera_running:
            if self.cap and self.cap.isOpened():
                self.camera_running = True
                self.camera_btn.configure(text="⏹ Stop Camera", fg_color=self.colors['error'])
                self.camera_status.configure(text="Camera Running", text_color=self.colors['success'])
                threading.Thread(target=self.camera_loop, daemon=True).start()
            else:
                messagebox.showerror("Error", "Camera not available")
        else:
            self.camera_running = False
            self.camera_btn.configure(text="▶ Start Camera", fg_color=self.colors['success'])
            self.camera_status.configure(text="Camera Stopped", text_color=self.colors['error'])
    
    def camera_loop(self):
        """Camera processing loop"""
        while self.camera_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    break
                    
                frame = cv2.flip(frame, 1)
                
                if not self.identified:
                    self.process_face_detection(frame)
                
                self.display_frame(frame)
                time.sleep(0.03)
                
            except Exception as e:
                self.log_status(f"Camera loop error: {e}", False)
                break
    
    def process_face_detection(self, frame):
        """Process face detection"""
        if not self.face_encodings:
            return
            
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame)
            encodings = face_recognition.face_encodings(rgb_frame, locations)
            
            for face_encoding in encodings:
                matches = face_recognition.compare_faces(self.face_encodings, face_encoding, tolerance=0.6)
                if True in matches:
                    match_index = matches.index(True)
                    name = self.face_names[match_index]
                    if not self.identified:
                        self.identified = True
                        self.person_name = name
                        self.greet_user(name)
                        self.enable_chat()
                        
        except Exception as e:
            self.log_status(f"Face detection error: {e}", False)
    
    def display_frame(self, frame):
        """Display camera frame"""
        try:
            # Resize frame
            frame = cv2.resize(frame, (700, 500))
            
            # Add premium status overlay
            status_text = f"Status: {'Identified: ' + self.person_name if self.identified else 'Looking for faces...'}"
            cv2.putText(frame, status_text, (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (79, 70, 229), 3)
            cv2.putText(frame, status_text, (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            # Convert to PhotoImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update camera label
            self.camera_label.configure(image=photo, text="")
            self.camera_label.image = photo  # Keep reference
            
        except Exception as e:
            self.log_status(f"Frame display error: {e}", False)
    
    def greet_user(self, name):
        """Greet user after recognition"""
        greeting = f"Hello {name}! I can see you. How can I help you today?"
        self.add_premium_chat_message("Bot", greeting, is_user=False)
        self.log_status(f"User identified and greeted: {name}")
        
        if self.voice_enabled and self.tts_engine:
            threading.Thread(target=lambda: self.tts_engine.say(greeting) or self.tts_engine.runAndWait(), daemon=True).start()
    
    def enable_chat(self):
        """Enable chat interface"""
        self.message_entry.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.message_entry.focus()
    
    def send_message(self, event=None):
        """Send user message"""
        if not self.identified:
            messagebox.showwarning("Warning", "Please wait for face recognition first!")
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Add user message
        self.add_premium_chat_message("User", message, is_user=True)
        
        # Clear input
        self.message_entry.delete(0, "end")
        
        # Start typing animation
        self.typing_indicator.start()
        
        # Process message in background
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def _direct_wikipedia_search(self, query: str) -> str:
        """
        Try to fetch a short summary from Wikipedia using the search API + page summary endpoint.
        Returns empty string if not found or on failure.
        """
        try:
            q = query.strip()
            if not q:
                return ""
            # Use opensearch-like search via action=query&list=search
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": q,
                "format": "json",
                "srlimit": 1
            }
            r = requests.get(search_url, params=params, headers=REQUEST_HEADERS, timeout=8)
            if r.status_code != 200:
                return ""
            data = r.json()
            hits = data.get("query", {}).get("search", [])
            if not hits:
                return ""
            title = hits[0].get("title")
            if not title:
                return ""
            # fetch summary using the REST endpoint (works better for extracts)
            safe_title = urllib.parse.quote(title.replace(" ", "_"))
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
            r2 = requests.get(summary_url, headers=REQUEST_HEADERS, timeout=8)
            if r2.status_code == 200:
                summary_json = r2.json()
                extract = summary_json.get("extract")
                # return short extract with citation note
                if extract:
                    excerpt = extract.strip()
                    return f"{excerpt} (Wikipedia)"
            # otherwise return empty
            return ""
        except Exception:
            return ""
    
    def process_message(self, message: str):
        """ENHANCED message processing with PRIORITY for current data"""
        try:
            print(f"Processing message: '{message}'")
            
            # Check for current data indicators FIRST
            current_keywords = [
                'current', 'now', 'today', 'latest', 'recent', 'present', 
                'as of', 'this year', 'in 2025', 'currently', 'up to date',
                'real time', 'live', 'who is', 'name of', 'what is', 'major events'
            ]
            
            lower_message = message.lower()
            is_current_query = any(keyword in lower_message for keyword in current_keywords)
            
            if is_current_query:
                print("🔥 CURRENT DATA QUERY DETECTED - Using real-time sources ONLY")
                
                if self.router and self.system_status['chatbot_modules']:
                    # Ask the router first
                    source, reply = self.router.route(message, self.chat_history)
                    
                    # If router returns AI (likely offline/knowledge-cutoff), try Wikipedia fallback for factual queries
                    if source == "ai":
                        # Try Wikipedia directly for up-to-date factual info
                        wiki_text = self._direct_wikipedia_search(message)
                        if wiki_text:
                            reply = wiki_text
                            source = "fact"
                        else:
                            # If Wikipedia didn't give anything, try news (gnews) for queries that look like news
                            try:
                                from chatbot import news as news_module
                                news_results = news_module.get_news(message)
                                if news_results and isinstance(news_results, list) and len(news_results) > 0 and not news_results[0].startswith("No news found"):
                                    reply = "\n".join(news_results)
                                    source = "gnews"
                                else:
                                    # final fallback system message
                                    reply = "I don't have a reliable up-to-date answer for this. Please check live news sources or official pages."
                                    source = "system"
                            except Exception:
                                reply = "I don't have a reliable up-to-date answer for this. Please check live news sources or official pages."
                                source = "system"
                    
                    tags = {
                        "system": " (Real-time message)",
                        "api": " (API)",
                        "gnews": " (GNews)",
                        "fact": " (Wikipedia)",
                        "ai": " (AI - Knowledge cutoff)"
                    }
                    full_response = reply + tags.get(source, "")
                else:
                    full_response = "I don't have access to real-time information systems right now. Please check current news sources, official websites, or recent publications for up-to-date information. (System)"
            
            else:
                # Regular processing for non-current queries
                print("📝 Regular query processing")
                
                if self.router and self.system_status['chatbot_modules']:
                    # Use modular router
                    source, reply = self.router.route(message, self.chat_history)
                    
                    # Tag responses with source
                    tags = {
                        "system": " (System)",
                        "api": " (API)", 
                        "gnews": " (GNews)",
                        "fact": " (DuckDuckGo/Wikipedia)",
                        "ai": " (AI Knowledge)"
                    }
                    
                    full_response = reply + tags.get(source, "")
                    
                    # Update chat history for context
                    if source in ("ai", "fact", "api", "gnews"):
                        self.chat_history.append({"role": "user", "content": message})
                        self.chat_history.append({"role": "assistant", "content": reply})
                        
                else:
                    # Fallback response when modules aren't loaded
                    full_response = "I'm sorry, my advanced features aren't available right now. (System)"
            
            # Schedule response display
            self.root.after(1500, lambda: self.show_bot_response(full_response))
                
        except Exception as e:
            error_response = f"Error processing request: {str(e)} (Error)"
            self.root.after(1500, lambda: self.show_bot_response(error_response))
            self.log_status(f"Message processing error: {e}", False)
    
    def show_bot_response(self, text):
        """Show bot response"""
        # Stop typing animation
        try:
            self.typing_indicator.stop()
        except Exception:
            pass
        
        # Add bot response
        self.add_premium_chat_message("Bot", text, is_user=False)
        
        # Text to speech
        if self.voice_enabled and self.tts_engine:
            clean_text = text.replace("🌤️", "").replace("📰", "").replace("📅", "").replace("📆", "")
            clean_text = clean_text.split(" (")[0]
            
            threading.Thread(
                target=lambda: self.tts_engine.say(clean_text) or self.tts_engine.runAndWait(), 
                daemon=True
            ).start()
    
    def cleanup(self):
        """Cleanup resources"""
        self.log_status("Shutting down Smart Vision Bot...")
        self.camera_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.log_status("Cleanup completed")

def main():
    root = ctk.CTk()
    app = SmartVisionBotGUI(root)
    
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
