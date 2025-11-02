import cv2
import numpy as np
import os

class FaceDetector:
    def __init__(self, confidence_threshold=0.7):
        """
        Initialize face detector with OpenCV DNN
        
        Args:
            confidence_threshold: Minimum confidence for face detection
        """
        self.confidence_threshold = confidence_threshold
        self.net = None
        self.load_model()
        
    def load_model(self):
        """Load pre-trained face detection model"""
        # Model files (will be downloaded automatically)
        prototxt_path = "models/deploy.prototxt"
        model_path = "models/res10_300x300_ssd_iter_140000.caffemodel"
        
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        
        # Download models if they don't exist
        if not os.path.exists(prototxt_path):
            self.download_model_files()
            
        try:
            # Load the DNN model
            self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            print("✅ Face detection model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load face detection model: {e}")
            print("Please run: python download_models.py")
            
    def download_model_files(self):
        """Download required model files"""
        import urllib.request
        
        print("📥 Downloading face detection models...")
        
        # URLs for model files
        prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        model_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        
        try:
            # Download prototxt
            urllib.request.urlretrieve(prototxt_url, "models/deploy.prototxt")
            print("✅ Downloaded deploy.prototxt")
            
            # Download model (this might take a while)
            print("📥 Downloading model file (10.6 MB)...")
            urllib.request.urlretrieve(model_url, "models/res10_300x300_ssd_iter_140000.caffemodel")
            print("✅ Downloaded model file")
            
        except Exception as e:
            print(f"❌ Failed to download models: {e}")
            print("Please download manually from OpenCV repository")
            
    def detect(self, frame):
        """
        Detect faces in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of (x, y, w, h) bounding boxes
        """
        if self.net is None:
            return []
            
        # Get frame dimensions
        (h, w) = frame.shape[:2]
        
        # Create blob from frame
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0)
        )
        
        # Pass blob through network
        self.net.setInput(blob)
        detections = self.net.forward()
        
        faces = []
        
        # Process detections
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            # Filter weak detections
            if confidence > self.confidence_threshold:
                # Get bounding box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x, y, x1, y1) = box.astype("int")
                
                # Convert to (x, y, w, h) format
                width = x1 - x
                height = y1 - y
                
                # Ensure coordinates are within frame bounds
                x = max(0, x)
                y = max(0, y)
                width = min(width, w - x)
                height = min(height, h - y)
                
                if width > 0 and height > 0:
                    faces.append((x, y, width, height))
                    
        return faces
        
    def detect_largest(self, frame):
        """
        Detect only the largest face in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            Single (x, y, w, h) tuple or None
        """
        faces = self.detect(frame)
        
        if not faces:
            return None
            
        # Return face with largest area
        largest = max(faces, key=lambda face: face[2] * face[3])
        return largest

# Standalone function for easy import
def detect_faces(frame, confidence=0.7):
    """
    Standalone function to detect faces
    
    Args:
        frame: Input image frame
        confidence: Detection confidence threshold
        
    Returns:
        List of (x, y, w, h) bounding boxes
    """
    detector = FaceDetector(confidence)
    return detector.detect(frame)