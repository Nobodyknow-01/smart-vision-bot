import cv2
import threading
import queue
import time

class VideoStream:
    def __init__(self, src=0, width=640, height=480, queue_size=5):
        """
        Initialize video stream with threading for smooth performance
        
        Args:
            src: Camera source (0 for default camera)
            width: Frame width
            height: Frame height  
            queue_size: Maximum frames to buffer
        """
        self.src = src
        self.cap = cv2.VideoCapture(src)
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Thread-safe queue
        self.Q = queue.Queue(maxsize=queue_size)
        self.stopped = False
        
        # Start capture thread
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()
        
        # Wait for first frame
        time.sleep(0.5)
        
    def update(self):
        """Continuously capture frames in background thread"""
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ Failed to read frame from camera")
                continue
                
            # Add frame to queue (drop oldest if full)
            if not self.Q.full():
                self.Q.put(frame)
            else:
                # Remove oldest frame and add new one
                try:
                    self.Q.get_nowait()
                    self.Q.put(frame)
                except queue.Empty:
                    pass
                    
    def read(self):
        """Get the latest frame from queue"""
        try:
            return self.Q.get(timeout=1.0)
        except queue.Empty:
            return None
            
    def is_opened(self):
        """Check if camera is opened"""
        return self.cap.isOpened()
        
    def stop(self):
        """Stop the video stream and cleanup"""
        self.stopped = True
        
        # Wait for thread to finish
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
            
        # Release camera
        if self.cap.isOpened():
            self.cap.release()
            
        print("📹 Video stream stopped")

    def __del__(self):
        """Cleanup on object destruction"""
        self.stop()