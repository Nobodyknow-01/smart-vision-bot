# 🤖 Smart Vision Bot  
*A next-generation AI-powered Assistant combining Computer Vision, NLP, and Voice Interaction*

---

### 🧠 Overview
**Smart Vision Bot** is an intelligent assistant that integrates:
- Real-time **face recognition** 🧍‍♂️  
- Smart **chat-based AI interaction** 💬  
- **Voice input/output** for hands-free operation 🎙️  
- Real-world APIs: **Weather**, **News**, **Finance**, and **Knowledge** 🌍  
- A modern **CustomTkinter GUI** with real-time camera feed and dynamic chat interface ✨  

---

### 🏗️ System Architecture

```mermaid
graph TD
A[User Interaction Layer<br>(CustomTkinter GUI)] --> B[Chat Router<br>(router.py)]
A --> C[Camera Module<br>(OpenCV + Face Recognition)]
A --> D[Voice I/O<br>(Speech-to-Text & pyttsx3 TTS)]
B --> E[Weather Module<br>(Open Meteo API)]
B --> F[News Module<br>(GNews API)]
B --> G[Knowledge/LLM Client<br>(Groq API / Wikipedia)]
C --> H[Face Recognition DB<br>(Encodings.pkl)]
E --> I[External APIs]
F --> I
G --> I
