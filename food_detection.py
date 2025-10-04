import cv2
import numpy as np
import time
import json
from threading import Lock
from flask import Response
import tensorflow as tf

class FoodDetector:
    def __init__(self, camera_index=0, model_path=None):
  
        self.camera_index = camera_index
        self.model_path = model_path
        self.model = None
        self.last_detection = None
        self.last_confidence = 0.0
        self.frame_lock = Lock()
        self.current_frame = None
        
        # Initialize camera
        self.init_camera()
        
        # Load ML model if available
        if model_path:
            self.load_model()
        
        # Load food categories
        self.load_food_categories()
        
        print("Food detector initialized successfully")
    
    def init_camera(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test camera
            ret, frame = self.cap.read()
            if not ret:
                raise RuntimeError("Failed to read from camera")
            
            print(f"Camera initialized: {self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
            
        except Exception as e:
            print(f"Camera initialization error: {e}")
            self.cap = None
    
    def load_model(self):
        """Load TensorFlow model for food classification"""
        try:
            # Try to load TensorFlow model
            self.model = tf.keras.models.load_model(self.model_path)
            print(f"Model loaded from {self.model_path}")
            
            # Get model input shape
            self.input_shape = self.model.input_shape[1:3]  # (height, width)
            print(f"Model input shape: {self.input_shape}")
            
        except Exception as e:
            print(f"Failed to load model: {e}")
            print("Falling back to rule-based detection")
            self.model = None
    
    def load_food_categories(self):
        """Load food categories and labels"""
        try:
            with open('data/food_categories.json', 'r') as f:
                self.food_categories = json.load(f)
        except FileNotFoundError:
            # Default food categories for rule-based detection
            self.food_categories = {
                'apple': {'color_range': [(0, 50, 50), (10, 255, 255)], 'shape': 'round'},
                'banana': {'color_range': [(15, 100, 100), (30, 255, 255)], 'shape': 'elongated'},
                'orange': {'color_range': [(5, 150, 150), (15, 255, 255)], 'shape': 'round'},
                'tomato': {'color_range': [(0, 150, 150), (5, 255, 255)], 'shape': 'round'},
                'carrot': {'color_range': [(10, 150, 150), (20, 255, 255)], 'shape': 'elongated'},
                'broccoli': {'color_range': [(35, 100, 100), (85, 255, 255)], 'shape': 'irregular'},
                'bread': {'color_range': [(15, 50, 100), (30, 150, 200)], 'shape': 'rectangular'},
                'unknown': {'color_range': [(0, 0, 0), (180, 255, 255)], 'shape': 'any'}
            }
            
            # Save default categories
            try:
                with open('data/food_categories.json', 'w') as f:
                    json.dump(self.food_categories, f, indent=2)
            except:
                pass
    
    def preprocess_image(self, image):
        """Preprocess image for model inference"""
        if self.model is None:
            return image
        
        # Resize to model input size
        processed = cv2.resize(image, self.input_shape)
        
        # Normalize pixel values
        processed = processed.astype(np.float32) / 255.0
        
        # Add batch dimension
        processed = np.expand_dims(processed, axis=0)
        
        return processed
    
    def detect_with_model(self, image):
        """Detect food using TensorFlow model"""
        try:
            processed_image = self.preprocess_image(image)
            predictions = self.model.predict(processed_image, verbose=0)
            
            # Get top prediction
            class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][class_idx])
            
            # Map class index to food name (you'll need to adjust this based on your model)
            class_names = list(self.food_categories.keys())
            if class_idx < len(class_names):
                food_item = class_names[class_idx]
            else:
                food_item = 'unknown'
            
            return {
                'food_item': food_item,
                'confidence': confidence,
                'method': 'ml_model'
            }
            
        except Exception as e:
            print(f"Model inference error: {e}")
            return None
    
    def detect_with_color(self, image):
        """Detect food using color-based rules"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            best_match = None
            best_score = 0
            
            for food_name, properties in self.food_categories.items():
                if food_name == 'unknown':
                    continue
                
                # Create color mask
                lower_bound = np.array(properties['color_range'][0])
                upper_bound = np.array(properties['color_range'][1])
                mask = cv2.inRange(hsv, lower_bound, upper_bound)
                
                # Calculate color match score
                color_pixels = cv2.countNonZero(mask)
                total_pixels = image.shape[0] * image.shape[1]
                color_ratio = color_pixels / total_pixels
                
                # Simple shape analysis
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest_contour)
                    
                    if area > 1000:  # Minimum area threshold
                        # Calculate shape score (simplified)
                        perimeter = cv2.arcLength(largest_contour, True)
                        if perimeter > 0:
                            circularity = 4 * np.pi * area / (perimeter * perimeter)
                            
                            # Score based on expected shape
                            shape_score = 1.0
                            if properties['shape'] == 'round' and circularity > 0.7:
                                shape_score = 1.2
                            elif properties['shape'] == 'elongated' and circularity < 0.5:
                                shape_score = 1.2
                            
                            total_score = color_ratio * shape_score
                            
                            if total_score > best_score and total_score > 0.1:
                                best_score = total_score
                                best_match = food_name
            
            if best_match:
                return {
                    'food_item': best_match,
                    'confidence': min(best_score, 1.0),
                    'method': 'color_detection'
                }
            else:
                return {
                    'food_item': 'unknown',
                    'confidence': 0.0,
                    'method': 'color_detection'
                }
                
        except Exception as e:
            print(f"Color detection error: {e}")
            return None
    
    def detect_food(self):
        """Main food detection method"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Store current frame for streaming
        with self.frame_lock:
            self.current_frame = frame.copy()
        
        # Crop to center region for better detection
        h, w = frame.shape[:2]
        crop_size = min(h, w) // 2
        center_x, center_y = w // 2, h // 2
        cropped = frame[
            center_y - crop_size//2:center_y + crop_size//2,
            center_x - crop_size//2:center_x + crop_size//2
        ]
        
        # Try ML model first, then fall back to color detection
        if self.model:
            result = self.detect_with_model(cropped)
        else:
            result = None
        
        if not result or result['confidence'] < 0.5:
            result = self.detect_with_color(cropped)
        
        # Update last detection
        if result:
            self.last_detection = result['food_item']
            self.last_confidence = result['confidence']
        
        return result
    
    def draw_detection_overlay(self, frame):
        """Draw detection results on frame"""
        if not frame is None:
            h, w = frame.shape[:2]
            
            # Draw detection area
            crop_size = min(h, w) // 2
            center_x, center_y = w // 2, h // 2
            
            cv2.rectangle(frame, 
                         (center_x - crop_size//2, center_y - crop_size//2),
                         (center_x + crop_size//2, center_y + crop_size//2),
                         (0, 255, 0), 2)
            
            # Draw detection text
            if self.last_detection and self.last_confidence > 0.3:
                text = f"{self.last_detection}: {self.last_confidence:.2f}"
                cv2.putText(frame, text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Draw timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, h - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def generate_stream(self):
        """Generate video stream with detection overlay"""
        def generate():
            while True:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # Add detection overlay
                        frame_with_overlay = self.draw_detection_overlay(frame)
                        
                        # Encode frame as JPEG
                        _, buffer = cv2.imencode('.jpg', frame_with_overlay, 
                                               [cv2.IMWRITE_JPEG_QUALITY, 85])
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                time.sleep(0.033)  # ~30 FPS
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def capture_image(self, filename=None):
        """Capture and save current frame"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if ret:
            if filename:
                cv2.imwrite(filename, frame)
                print(f"Image saved: {filename}")
            return frame
        
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.cap:
                self.cap.release()
            print("Food detector cleanup complete")
        except Exception as e:
            print(f"Error during cleanup: {e}")


# Test script
if __name__ == '__main__':
    import sys
    
    detector = FoodDetector(camera_index=0)
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'test':
            print("=== Food Detection Test ===")
            print("Press 'q' to quit, 's' to save image, 'd' to detect")
            
            while True:
                ret, frame = detector.cap.read()
                if ret:
                    # Add overlay
                    frame_with_overlay = detector.draw_detection_overlay(frame)
                    cv2.imshow('Food Detection', frame_with_overlay)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        filename = f"capture_{int(time.time())}.jpg"
                        detector.capture_image(filename)
                    elif key == ord('d'):
                        result = detector.detect_food()
                        if result:
                            print(f"Detected: {result}")
            
            cv2.destroyAllWindows()
        
        else:
            print("=== Continuous Detection ===")
            print("Press Ctrl+C to stop")
            
            while True:
                result = detector.detect_food()
                if result and result['confidence'] > 0.3:
                    print(f"Detected: {result['food_item']} "
                          f"(confidence: {result['confidence']:.2f}, "
                          f"method: {result['method']})")
                
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        detector.cleanup()