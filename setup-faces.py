import face_recognition
import os
import pickle
import cv2
from PIL import Image
import numpy as np

def create_face_encodings():
    """Create face encodings from images in the faces/ directory"""
    
    # Create faces directory if it doesn't exist
    faces_dir = "faces"
    if not os.path.exists(faces_dir):
        os.makedirs(faces_dir)
        print(f"Created {faces_dir} directory")
        print("Please add face images (JPG/PNG) to this directory.")
        print("Name format: PersonName.jpg (e.g., Alice.jpg, Bob.png)")
        return
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    
    for file in os.listdir(faces_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    if not image_files:
        print("No image files found in faces/ directory")
        print("Please add face images (JPG/PNG) and run again.")
        return
    
    print(f"Found {len(image_files)} image files")
    
    encodings = []
    names = []
    
    for image_file in image_files:
        print(f"Processing {image_file}...")
        
        try:
            # Load image
            image_path = os.path.join(faces_dir, image_file)
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                print(f"  ❌ No face detected in {image_file}")
                continue
            
            if len(face_encodings) > 1:
                print(f"  ⚠ Multiple faces detected in {image_file}, using first one")
            
            # Use the first face encoding
            encoding = face_encodings[0]
            
            # Extract name from filename (remove extension)
            name = os.path.splitext(image_file)[0]
            
            encodings.append(encoding)
            names.append(name)
            
            print(f"  ✓ Successfully encoded face for {name}")
            
        except Exception as e:
            print(f"  ❌ Error processing {image_file}: {e}")
            continue
    
    if not encodings:
        print("No face encodings created. Please check your images.")
        return
    
    # Save encodings
    data = {
        'encodings': encodings,
        'names': names
    }
    
    with open('encodings.pkl', 'wb') as f:
        pickle.dump(data, f)
    
    print(f"\n✓ Successfully created encodings for {len(names)} people:")
    for name in names:
        print(f"  - {name}")
    
    print(f"\nEncodings saved to encodings.pkl")
    print("You can now run the Smart Vision Bot!")

def test_face_recognition():
    """Test the face recognition with a sample image"""
    
    if not os.path.exists('encodings.pkl'):
        print("No encodings file found. Please run create_face_encodings() first.")
        return
    
    # Load encodings
    with open('encodings.pkl', 'rb') as f:
        data = pickle.load(f)
        known_encodings = data['encodings']
        known_names = data['names']
    
    print(f"Loaded encodings for: {', '.join(known_names)}")
    
    # Test with webcam
    print("Testing with webcam... Press 'q' to quit")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Could not open webcam")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces and encodings
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Draw rectangles and names
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare with known faces
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"
            
            if True in matches:
                match_index = matches.index(True)
                name = known_names[match_index]
            
            # Draw rectangle and name
            top, right, bottom, left = face_location
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        
        # Display frame
        cv2.imshow('Face Recognition Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    """Main function"""
    print("=" * 50)
    print("Smart Vision Bot - Face Encoding Setup")
    print("=" * 50)
    
    choice = input("\nChoose an option:\n1. Create face encodings\n2. Test face recognition\n\nEnter choice (1 or 2): ")
    
    if choice == '1':
        create_face_encodings()
    elif choice == '2':
        test_face_recognition()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()