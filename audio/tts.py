import pyttsx3
import threading
import time
from queue import Queue, Empty

class TTSEngine:
    def __init__(self):
        """Initialize TTS engine"""
        self.engine = None
        self.speech_queue = Queue()
        self.is_speaking = False
        self.speech_thread = None
        self.stop_speaking = False
        
        self.initialize_engine()
        
    def initialize_engine(self):
        """Initialize pyttsx3 engine with optimal settings"""
        try:
            self.engine = pyttsx3.init()
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            # Set voice properties
            if voices:
                # Try to use a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)
                    
            # Set speech rate (words per minute)
            self.engine.setProperty('rate', 180)  # Slightly faster than default
            
            # Set volume (0.0 to 1.0)
            self.engine.setProperty('volume', 0.9)
            
            print("✅ TTS engine initialized successfully")
            
            # Start speech processing thread
            self.start_speech_thread()
            
        except Exception as e:
            print(f"❌ TTS initialization failed: {e}")
            print("💡 Try installing: pip install pyttsx3")
            self.engine = None
            
    def start_speech_thread(self):
        """Start background thread for speech processing"""
        if self.speech_thread is None or not self.speech_thread.is_alive():
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()
            
    def _speech_worker(self):
        """Background worker for processing speech queue"""
        while not self.stop_speaking:
            try:
                # Get text from queue (with timeout)
                text = self.speech_queue.get(timeout=1.0)
                
                if text and self.engine:
                    self.is_speaking = True
                    
                    # Speak the text
                    self.engine.say(text)
                    self.engine.runAndWait()
                    
                    self.is_speaking = False
                    
                self.speech_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                print(f"❌ TTS error: {e}")
                self.is_speaking = False
                
    def speak(self, text: str, interrupt: bool = False):
        """
        Add text to speech queue
        
        Args:
            text: Text to speak
            interrupt: Whether to interrupt current speech
        """
        if not self.engine:
            print(f"🤖: {text}")  # Fallback to text output
            return
            
        if not text or not text.strip():
            return
            
        # Clean text for better speech
        clean_text = self._clean_text_for_speech(text)
        
        if interrupt:
            self.stop_current_speech()
            
        # Add to queue
        self.speech_queue.put(clean_text)
        
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        # Remove emojis and special characters
        import re
        
        # Remove emoji patterns
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map
                                 u"\U0001F1E0-\U0001F1FF"  # flags
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251"
                                 "]+", flags=re.UNICODE)
        
        text = emoji_pattern.sub('', text)
        
        # Replace common symbols with words
        replacements = {
            '°C': ' degrees Celsius',
            '°F': ' degrees Fahrenheit',
            '%': ' percent',
            '&': ' and ',
            '@': ' at ',
            '#': ' hash ',
            '$': ' dollars ',
            '€': ' euros ',
            '£': ' pounds ',
            '₹': ' rupees ',
            '...': ' ',
            '..': ' ',
            '  ': ' '  # Double spaces to single
        }
        
        for symbol, word in replacements.items():
            text = text.replace(symbol, word)
            
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
        
    def stop_current_speech(self):
        """Stop current speech immediately"""
        if self.engine and self.is_speaking:
            try:
                self.engine.stop()
                
                # Clear the queue
                while not self.speech_queue.empty():
                    try:
                        self.speech_queue.get_nowait()
                    except Empty:
                        break
                        
                self.is_speaking = False
                print("🔇 Speech interrupted")
                
            except Exception as e:
                print(f"❌ Error stopping speech: {e}")
                
    def is_busy(self) -> bool:
        """Check if TTS is currently speaking"""
        return self.is_speaking or not self.speech_queue.empty()
        
    def wait_until_done(self, timeout: float = 10.0):
        """Wait until all speech is completed"""
        start_time = time.time()
        
        while self.is_busy() and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        if self.engine:
            self.engine.setProperty('rate', rate)
            print(f"🗣️ Speech rate set to {rate} WPM")
            
    def set_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        if self.engine:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.engine.setProperty('volume', volume)
            print(f"🔊 Volume set to {volume:.1f}")
            
    def list_voices(self):
        """List available voices"""
        if not self.engine:
            print("❌ TTS engine not available")
            return
            
        voices = self.engine.getProperty('voices')
        
        if voices:
            print("🎤 Available voices:")
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})")
        else:
            print("❌ No voices available")
            
    def set_voice(self, voice_index: int):
        """Set voice by index"""
        if not self.engine:
            return
            
        voices = self.engine.getProperty('voices')
        
        if voices and 0 <= voice_index < len(voices):
            self.engine.setProperty('voice', voices[voice_index].id)
            print(f"🎤 Voice changed to: {voices[voice_index].name}")
        else:
            print(f"❌ Invalid voice index: {voice_index}")
            
    def test_speech(self):
        """Test TTS functionality"""
        test_messages = [
            "Hello! I am your Smart Vision Bot.",
            "Testing text to speech functionality.",
            "The weather is 25 degrees Celsius today.",
            "Speech synthesis is working correctly!"
        ]
        
        print("🎤 Testing TTS engine...")
        for msg in test_messages:
            print(f"Speaking: {msg}")
            self.speak(msg)
            self.wait_until_done()
            time.sleep(0.5)
            
        print("✅ TTS test completed!")
        
    def cleanup(self):
        """Clean up TTS resources"""
        self.stop_speaking = True
        
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2.0)
            
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
                
        print("🔇 TTS engine cleaned up")

# Standalone functions
def speak_text(text: str):
    """Quick function to speak text"""
    engine = TTSEngine()
    engine.speak(text)
    engine.wait_until_done()
    engine.cleanup()

def test_tts():
    """Test TTS functionality"""
    print("🎤 TTS Test Starting...")
    
    tts = TTSEngine()
    
    if tts.engine:
        tts.list_voices()
        tts.test_speech()
    else:
        print("❌ TTS not available")
        
    tts.cleanup()

if __name__ == "__main__":
    test_tts()