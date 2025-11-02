import os
import face_recognition
import pickle
import cv2
from pathlib import Path

def encode_faces():
    """
    Create face encodings from images in faces/ directory
    Saves encodings to encodings.pkl
    """
    print("🔍 Starting face encoding process...")
    
    # Create faces directory if it doesn't exist
    faces_dir = Path("faces")
    faces_dir.mkdir(exist_ok=True)
    
    if not any(faces_dir.iterdir()):
        print("❌ No images found in faces/ directory!")
        print("📁 Please add images to faces/ directory with format: PersonName.jpg")
        print("💡 Example: faces/John.jpg, faces/Alice.jpg")
        return False
    
    known_encodings = []
    known_names = []
    
    # Process each image in faces directory
    for image_path in faces_dir.glob("*"):
        if image_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            # Get person name from filename
            person_name = image_path.stem
            
            print(f"🔄 Processing {person_name}...")
            
            try:
                # Load image
                image = face_recognition.load_image_file(str(image_path))
                
                # Get face encodings
                encodings = face_recognition.face_encodings(image)
                
                if len(encodings) == 0:
                    print(f"❌ No face found in {image_path.name}")
                    continue
                elif len(encodings) > 1:
                    print(f"⚠️ Multiple faces found in {image_path.name}, using first one")
                
                # Add encoding and name
                known_encodings.append(encodings[0])
                known_names.append(person_name)
                
                print(f"✅ Encoded {person_name}")
                
            except Exception as e:
                print(f"❌ Error processing {image_path.name}: {e}")
    
    if not known_encodings:
        print("❌ No valid face encodings created!")
        return False
    
    # Save encodings
    encodings_data = {
        "encodings": known_encodings,
        "names": known_names
    }
    
    try:
        with open("encodings.pkl", "wb") as f:
            pickle.dump(encodings_data, f)
        
        print(f"✅ Successfully encoded {len(known_encodings)} faces")
        print(f"📁 Encodings saved to encodings.pkl")
        
        # Print summary
        print("\n📋 Encoded faces:")
        for name in known_names:
            print(f"  • {name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to save encodings: {e}")
        return False

def validate_encodings():
    """Validate saved encodings"""
    try:
        with open("encodings.pkl", "rb") as f:
            data = pickle.load(f)
            
        print(f"✅ Encodings file is valid")
        print(f"📊 Contains {len(data['encodings'])} face encodings")
        print(f"👥 Names: {', '.join(data['names'])}")
        return True
        
    except Exception as e:
        print(f"❌ Invalid encodings file: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SMART VISION BOT - FACE ENCODER")
    print("=" * 50)
    
    # Check if faces directory exists and has images
    faces_dir = Path("faces")
    if not faces_dir.exists():
        faces_dir.mkdir()
        print("📁 Created faces/ directory")
        print("📝 Add your photos (JPG/PNG) to faces/ directory")
        print("📝 Name format: PersonName.jpg (e.g., John.jpg, Alice.jpg)")
        exit(1)
    
    # List existing images
    image_files = list(faces_dir.glob("*.jpg")) + list(faces_dir.glob("*.jpeg")) + list(faces_dir.glob("*.png"))
    
    if not image_files:
        print("❌ No image files found in faces/ directory")
        print("📝 Add photos with extensions: .jpg, .jpeg, .png")
        print("📝 Name format: PersonName.jpg")
        exit(1)
    
    print(f"📸 Found {len(image_files)} image(s):")
    for img in image_files:
        print(f"  • {img.name}")
    
    print("\n🚀 Starting encoding process...")
    success = encode_faces()
    
    if success:
        print("\n🎉 Face encoding completed successfully!")
        print("🚀 You can now run: python app.py")
    else:
        print("\n❌ Face encoding failed!")
        print("🔧 Please check your images and try again")
    
    print("=" * 50)