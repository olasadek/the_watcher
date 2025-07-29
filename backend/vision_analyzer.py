import cv2
import numpy as np
from datetime import datetime
import json
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionAnalyzer:
    """
    Free computer vision analyzer for incident detection
    Uses OpenCV and traditional computer vision techniques
    """
    
    def __init__(self):
        # Initialize background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=50
        )
        
        # Initialize HOG person detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Load face cascade for face detection
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except:
            logger.warning("Face cascade not loaded - face detection disabled")
            self.face_cascade = None
        
        # Previous frame for motion analysis
        self.prev_frame = None
        self.frame_count = 0
        
        # Detection thresholds
        self.motion_threshold = 5000
        self.person_confidence_threshold = 0.5
        self.fall_aspect_ratio_threshold = 1.5
        
    def analyze_frame(self, frame: np.ndarray) -> Dict:
        """
        Analyze a single frame for various incidents
        
        Args:
            frame: Input image as numpy array
            
        Returns:
            Dict containing analysis results
        """
        self.frame_count += 1
        results = {
            "frame_id": self.frame_count,
            "timestamp": datetime.utcnow().isoformat(),
            "incidents_detected": [],
            "analysis_details": {}
        }
        
        try:
            # Resize frame for faster processing
            height, width = frame.shape[:2]
            if width > 640:
                scale = 640 / width
                new_width = 640
                new_height = int(height * scale)
                frame_resized = cv2.resize(frame, (new_width, new_height))
            else:
                frame_resized = frame.copy()
            
            # Convert to grayscale for some operations
            gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            
            # 1. Motion Detection
            motion_detected, motion_area = self._detect_motion(frame_resized)
            results["analysis_details"]["motion"] = {
                "detected": motion_detected,
                "area": motion_area
            }
            
            # 2. Person Detection
            persons = self._detect_persons(frame_resized)
            results["analysis_details"]["persons"] = {
                "count": len(persons),
                "locations": persons
            }
            
            # 3. Fall Detection (based on person orientation)
            if persons:
                fallen_persons = self._detect_fallen_persons(persons)
                if fallen_persons:
                    results["incidents_detected"].append({
                        "type": "person_fallen",
                        "confidence": 0.8,
                        "locations": fallen_persons,
                        "severity": "high"
                    })
            
            # 4. Fight Detection (rapid motion + multiple persons)
            if len(persons) >= 2 and motion_detected and motion_area > 15000:
                fight_confidence = self._analyze_fight_behavior(persons, motion_area)
                if fight_confidence > 0.6:
                    results["incidents_detected"].append({
                        "type": "fight",
                        "confidence": fight_confidence,
                        "persons_involved": len(persons),
                        "severity": "high"
                    })
            
            # 5. Suspicious Activity Detection (loitering, unusual patterns)
            if motion_detected:
                suspicious_score = self._detect_suspicious_activity(motion_area, len(persons))
                if suspicious_score > 0.7:
                    results["incidents_detected"].append({
                        "type": "suspicious_activity",
                        "confidence": suspicious_score,
                        "severity": "medium"
                    })
            
            # 6. Smoking Detection (placeholder - would need more sophisticated ML)
            smoking_detected = self._detect_smoking_placeholder(frame_resized, persons)
            if smoking_detected:
                results["incidents_detected"].append({
                    "type": "smoking",
                    "confidence": 0.6,
                    "severity": "low"
                })
            
            # Store current frame for next iteration
            self.prev_frame = gray.copy()
            
        except Exception as e:
            logger.error(f"Error in frame analysis: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _detect_motion(self, frame: np.ndarray) -> Tuple[bool, int]:
        """Detect motion using background subtraction"""
        try:
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Remove noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            
            # Calculate motion area
            motion_area = cv2.countNonZero(fg_mask)
            
            # Detect significant motion
            motion_detected = motion_area > self.motion_threshold
            
            return motion_detected, motion_area
            
        except Exception as e:
            logger.error(f"Motion detection error: {str(e)}")
            return False, 0
    
    def _detect_persons(self, frame: np.ndarray) -> List[Dict]:
        """Detect persons using HOG detector"""
        try:
            # Detect people
            boxes, weights = self.hog.detectMultiScale(
                frame, 
                winStride=(8, 8),
                padding=(32, 32),
                scale=1.05
            )
            
            persons = []
            for (x, y, w, h), weight in zip(boxes, weights):
                if weight > self.person_confidence_threshold:
                    persons.append({
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "confidence": float(weight),
                        "center": [int(x + w/2), int(y + h/2)],
                        "aspect_ratio": h / w if w > 0 else 0
                    })
            
            return persons
            
        except Exception as e:
            logger.error(f"Person detection error: {str(e)}")
            return []
    
    def _detect_fallen_persons(self, persons: List[Dict]) -> List[Dict]:
        """Detect fallen persons based on aspect ratio"""
        fallen = []
        
        for person in persons:
            aspect_ratio = person["aspect_ratio"]
            
            # A fallen person typically has a lower aspect ratio (wider than tall)
            if aspect_ratio < (1 / self.fall_aspect_ratio_threshold):
                fallen.append({
                    "bbox": person["bbox"],
                    "confidence": 0.8,
                    "aspect_ratio": aspect_ratio
                })
        
        return fallen
    
    def _analyze_fight_behavior(self, persons: List[Dict], motion_area: int) -> float:
        """Analyze if the scene suggests a fight"""
        if len(persons) < 2:
            return 0.0
        
        # Calculate proximity between persons
        fight_score = 0.0
        
        for i, person1 in enumerate(persons):
            for j, person2 in enumerate(persons[i+1:], i+1):
                # Calculate distance between person centers
                x1, y1 = person1["center"]
                x2, y2 = person2["center"]
                distance = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # If persons are close and there's significant motion
                if distance < 100 and motion_area > 20000:
                    fight_score += 0.4
        
        # Normalize score
        fight_score = min(fight_score, 1.0)
        
        return fight_score
    
    def _detect_suspicious_activity(self, motion_area: int, person_count: int) -> float:
        """Detect suspicious activity patterns"""
        suspicious_score = 0.0
        
        # Moderate motion with few people might indicate loitering
        if 3000 < motion_area < 8000 and person_count <= 2:
            suspicious_score += 0.3
        
        # Very high motion might indicate unusual activity
        if motion_area > 25000:
            suspicious_score += 0.5
        
        return min(suspicious_score, 1.0)
    
    def _detect_smoking_placeholder(self, frame: np.ndarray, persons: List[Dict]) -> bool:
        """
        Placeholder for smoking detection
        In a real implementation, this would use more sophisticated ML models
        """
        # For demo purposes, randomly detect smoking sometimes
        import random
        return len(persons) > 0 and random.random() < 0.1
    
    def get_annotated_frame(self, frame: np.ndarray, analysis_results: Dict) -> np.ndarray:
        """
        Draw annotations on frame based on analysis results
        """
        annotated = frame.copy()
        
        try:
            # Draw person detections
            persons = analysis_results.get("analysis_details", {}).get("persons", {}).get("locations", [])
            for person in persons:
                x, y, w, h = person["bbox"]
                cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(annotated, f"Person {person['confidence']:.2f}", 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw incident alerts
            incidents = analysis_results.get("incidents_detected", [])
            for i, incident in enumerate(incidents):
                y_pos = 30 + (i * 25)
                color = (0, 0, 255) if incident["severity"] == "high" else (0, 255, 255)
                text = f"{incident['type']}: {incident['confidence']:.2f}"
                cv2.putText(annotated, text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(annotated, timestamp, (10, frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        except Exception as e:
            logger.error(f"Annotation error: {str(e)}")
        
        return annotated

# Global analyzer instance
analyzer = VisionAnalyzer()

def analyze_image_data(image_data: bytes) -> Dict:
    """
    Analyze image data and return incident detection results
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dict with analysis results
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Invalid image data"}
        
        # Analyze frame
        results = analyzer.analyze_frame(frame)
        
        return results
        
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return {"error": str(e)}