# recognize.py
"""
Face Recognition helper for Smart Vision Bot
- Added reset() method to clear state
"""

import face_recognition
import os
import cv2

class FaceRecognizer:
    def __init__(self, encodings_dir="encodings"):
        self.encodings_dir = encodings_dir
        self.known_encodings = []
        self.known_names = []
        self._load_encodings()
        self.last_identity = None

    def _load_encodings(self):
        for file in os.listdir(self.encodings_dir):
            if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
                img = face_recognition.load_image_file(os.path.join(self.encodings_dir, file))
                encs = face_recognition.face_encodings(img)
                if encs:
                    self.known_encodings.append(encs[0])
                    self.known_names.append(os.path.splitext(file)[0])

    def recognize(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        encs = face_recognition.face_encodings(rgb, boxes)

        for enc, box in zip(encs, boxes):
            matches = face_recognition.compare_faces(self.known_encodings, enc, tolerance=0.45)
            if True in matches:
                idx = matches.index(True)
                name = self.known_names[idx]
                self.last_identity = name
                return name, box
        return None, None

    def reset(self):
        """Reset recognition state (forces re-identification)."""
        self.last_identity = None
