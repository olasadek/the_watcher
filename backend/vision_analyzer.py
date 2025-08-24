import cv2
import numpy as np
from datetime import datetime
import json
import logging
from typing import Dict, List, Tuple, Optional
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the dynamic context agent
try:
    from dynamic_context_agent import dynamic_context_agent
except ImportError:
    logger.warning("Dynamic context agent not available")
    dynamic_context_agent = None

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
        
        # Detection thresholds (now dynamic - will be updated by context agent)
        self.motion_threshold = 5000
        self.person_confidence_threshold = 0.5
        self.fall_aspect_ratio_threshold = 1.5
        
        # Base crowd analysis parameters (will be adjusted dynamically)
        self.base_crowd_density_threshold = 5  # persons per unit area
        self.base_gathering_size_threshold = 8  # minimum persons for unusual gathering
        self.base_max_normal_density = 10  # maximum normal crowd density
        
        # Dynamic thresholds (updated by context agent)
        self.crowd_density_threshold = self.base_crowd_density_threshold
        self.gathering_size_threshold = self.base_gathering_size_threshold
        self.max_normal_density = self.base_max_normal_density
        
        # Context tracking
        self.last_context_update = None
        self.context_reasoning = []
        
        # Crowd tracking
        self.crowd_history = []
        self.gathering_start_time = None
        self.last_crowd_count = 0
        
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
            
            # 7. Crowd Analysis
            crowd_analysis = self._analyze_crowd_density(persons, frame_resized.shape[:2])
            results["analysis_details"]["crowd"] = crowd_analysis
            
            # Check for crowd-related incidents
            if crowd_analysis["density_alert"]:
                results["incidents_detected"].append({
                    "type": "high_crowd_density",
                    "confidence": 0.9,
                    "crowd_count": len(persons),
                    "density": crowd_analysis["density"],
                    "severity": "medium"
                })
            
            if crowd_analysis["unusual_gathering"]:
                results["incidents_detected"].append({
                    "type": "unusual_gathering",
                    "confidence": 0.8,
                    "crowd_count": len(persons),
                    "duration": crowd_analysis["gathering_duration"],
                    "severity": "medium"
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
    
    def _analyze_crowd_density(self, persons: List[Tuple], frame_shape: Tuple) -> Dict:
        """
        Analyze crowd density and detect unusual gatherings
        
        Args:
            persons: List of detected person bounding boxes
            frame_shape: (height, width) of the frame
            
        Returns:
            Dict containing crowd analysis results
        """
        try:
            current_time = datetime.utcnow()
            person_count = len(persons)
            
            # Calculate frame area (in arbitrary units)
            frame_area = frame_shape[0] * frame_shape[1] / 10000  # normalize
            
            # Calculate crowd density (persons per unit area)
            density = person_count / frame_area if frame_area > 0 else 0
            
            # Update crowd history
            self.crowd_history.append({
                "timestamp": current_time,
                "count": person_count,
                "density": density
            })
            
            # Keep only recent history (last 60 seconds)
            cutoff_time = current_time.timestamp() - 60
            self.crowd_history = [
                record for record in self.crowd_history 
                if record["timestamp"].timestamp() > cutoff_time
            ]
            
            # Analyze gathering duration
            gathering_duration = 0
            unusual_gathering = False
            
            if person_count >= self.gathering_size_threshold:
                if self.gathering_start_time is None:
                    self.gathering_start_time = current_time
                else:
                    gathering_duration = (current_time - self.gathering_start_time).total_seconds()
                    if gathering_duration > self.gathering_duration_threshold:
                        unusual_gathering = True
            else:
                self.gathering_start_time = None
            
            # Check for density alerts
            density_alert = density > self.max_normal_density
            
            # Calculate average density over time
            avg_density = 0
            if self.crowd_history:
                avg_density = sum(record["density"] for record in self.crowd_history) / len(self.crowd_history)
            
            # Detect crowd movement patterns
            crowd_stability = self._analyze_crowd_stability()
            
            self.last_crowd_count = person_count
            
            return {
                "person_count": person_count,
                "density": round(density, 2),
                "avg_density": round(avg_density, 2),
                "density_alert": density_alert,
                "unusual_gathering": unusual_gathering,
                "gathering_duration": round(gathering_duration, 1),
                "crowd_stability": crowd_stability,
                "risk_level": self._calculate_crowd_risk_level(density, person_count, unusual_gathering)
            }
            
        except Exception as e:
            logger.error(f"Error in crowd analysis: {str(e)}")
            return {
                "person_count": len(persons),
                "density": 0,
                "avg_density": 0,
                "density_alert": False,
                "unusual_gathering": False,
                "gathering_duration": 0,
                "crowd_stability": "unknown",
                "risk_level": "low"
            }
    
    def _analyze_crowd_stability(self) -> str:
        """
        Analyze how stable the crowd is (static vs dynamic)
        
        Returns:
            String indicating crowd stability
        """
        if len(self.crowd_history) < 5:
            return "insufficient_data"
        
        recent_counts = [record["count"] for record in self.crowd_history[-5:]]
        count_variance = np.var(recent_counts) if len(recent_counts) > 1 else 0
        
        if count_variance < 2:
            return "stable"  # Very little change in crowd size
        elif count_variance < 10:
            return "moderate"  # Some fluctuation
        else:
            return "dynamic"  # High fluctuation
    
    def _calculate_crowd_risk_level(self, density: float, count: int, unusual_gathering: bool) -> str:
        """
        Calculate overall risk level based on crowd metrics
        
        Args:
            density: Current crowd density
            count: Number of people
            unusual_gathering: Whether there's an unusual gathering
            
        Returns:
            Risk level as string
        """
        risk_score = 0
        
        # Density contribution
        if density > self.max_normal_density:
            risk_score += 3
        elif density > self.max_normal_density * 0.7:
            risk_score += 2
        elif density > self.max_normal_density * 0.5:
            risk_score += 1
        
        # Count contribution
        if count > 20:
            risk_score += 3
        elif count > 15:
            risk_score += 2
        elif count > 10:
            risk_score += 1
        
        # Gathering contribution
        if unusual_gathering:
            risk_score += 2
        
        # Determine risk level
        if risk_score >= 6:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"
    
    def get_crowd_statistics(self) -> Dict:
        """
        Get comprehensive crowd statistics
        
        Returns:
            Dict containing crowd statistics
        """
        if not self.crowd_history:
            return {
                "total_observations": 0,
                "max_crowd_size": 0,
                "avg_crowd_size": 0,
                "max_density": 0,
                "avg_density": 0,
                "current_crowd_size": 0
            }
        
        counts = [record["count"] for record in self.crowd_history]
        densities = [record["density"] for record in self.crowd_history]
        
        return {
            "total_observations": len(self.crowd_history),
            "max_crowd_size": max(counts),
            "avg_crowd_size": round(sum(counts) / len(counts), 1),
            "max_density": round(max(densities), 2),
            "avg_density": round(sum(densities) / len(densities), 2),
            "current_crowd_size": self.last_crowd_count
        }
    
    async def update_dynamic_thresholds(self, current_time: Optional[datetime] = None) -> Dict:
        """
        Update crowd thresholds based on dynamic context (prayer times, events, location)
        This is where GPS agent communicates with crowd analysis agent for adaptive thresholds
        """
        if dynamic_context_agent is None:
            logger.warning("Dynamic context agent not available, using static thresholds")
            return {
                "status": "static",
                "thresholds": {
                    "crowd_density_threshold": self.crowd_density_threshold,
                    "gathering_size_threshold": self.gathering_size_threshold,
                    "max_normal_density": self.max_normal_density
                }
            }
        
        try:
            if current_time is None:
                current_time = datetime.now()
            
            # Get dynamic thresholds from context agent
            context_result = await dynamic_context_agent.get_dynamic_thresholds(current_time)
            
            # Update our thresholds
            new_thresholds = context_result['thresholds']
            
            self.crowd_density_threshold = new_thresholds['crowd_density']
            self.gathering_size_threshold = new_thresholds['gathering_size']
            self.max_normal_density = new_thresholds['max_normal_density']
            
            # Store context reasoning for logging
            self.context_reasoning = context_result['adjustments']
            self.last_context_update = current_time
            
            logger.info(f"Dynamic thresholds updated:")
            logger.info(f"  Crowd density: {self.base_crowd_density_threshold} → {self.crowd_density_threshold}")
            logger.info(f"  Gathering size: {self.base_gathering_size_threshold} → {self.gathering_size_threshold}")
            logger.info(f"  Max normal density: {self.base_max_normal_density} → {self.max_normal_density}")
            logger.info(f"  Reasoning: {', '.join(self.context_reasoning)}")
            
            if context_result['is_prayer_time']:
                logger.info(f"🕌 Prayer time detected: {context_result['prayer_info']}")
            
            return {
                "status": "updated",
                "context_result": context_result,
                "previous_thresholds": {
                    "crowd_density_threshold": self.base_crowd_density_threshold,
                    "gathering_size_threshold": self.base_gathering_size_threshold,
                    "max_normal_density": self.base_max_normal_density
                },
                "new_thresholds": {
                    "crowd_density_threshold": self.crowd_density_threshold,
                    "gathering_size_threshold": self.gathering_size_threshold,
                    "max_normal_density": self.max_normal_density
                },
                "reasoning": self.context_reasoning
            }
            
        except Exception as e:
            logger.error(f"Error updating dynamic thresholds: {e}")
            return {
                "status": "error",
                "error": str(e),
                "thresholds": {
                    "crowd_density_threshold": self.crowd_density_threshold,
                    "gathering_size_threshold": self.gathering_size_threshold,
                    "max_normal_density": self.max_normal_density
                }
            }
    
    async def update_camera_specific_thresholds(self, camera_id: str, current_time: Optional[datetime] = None) -> Dict:
        """
        Update crowd thresholds specific to a camera based on its country and active events
        This enables country-specific threshold adjustments for events
        """
        if dynamic_context_agent is None:
            logger.warning("Dynamic context agent not available, using static thresholds")
            return {
                "status": "static",
                "camera_id": camera_id,
                "thresholds": {
                    "crowd_density_threshold": self.crowd_density_threshold,
                    "gathering_size_threshold": self.gathering_size_threshold,
                    "max_normal_density": self.max_normal_density
                }
            }
        
        try:
            if current_time is None:
                current_time = datetime.now()
            
            # Get camera-specific dynamic thresholds from context agent
            context_result = await dynamic_context_agent.get_camera_specific_thresholds(camera_id, current_time)
            
            # Store original thresholds
            original_thresholds = {
                "crowd_density_threshold": self.crowd_density_threshold,
                "gathering_size_threshold": self.gathering_size_threshold,
                "max_normal_density": self.max_normal_density
            }
            
            # Update our thresholds for this camera
            new_thresholds = context_result['thresholds']
            
            self.crowd_density_threshold = new_thresholds['crowd_density']
            self.gathering_size_threshold = new_thresholds['gathering_size']
            self.max_normal_density = new_thresholds['max_normal_density']
            
            # Store context reasoning for logging
            self.context_reasoning = context_result['adjustments']
            self.last_context_update = current_time
            
            logger.info(f"Camera-specific thresholds updated for {camera_id} (Country: {context_result['camera_country']}):")
            logger.info(f"  Crowd density: {self.base_crowd_density_threshold} → {self.crowd_density_threshold}")
            logger.info(f"  Gathering size: {self.base_gathering_size_threshold} → {self.gathering_size_threshold}")
            logger.info(f"  Max normal density: {self.base_max_normal_density} → {self.max_normal_density}")
            logger.info(f"  Reasoning: {', '.join(self.context_reasoning)}")
            
            if context_result['is_prayer_time']:
                logger.info(f"🕌 Prayer time detected: {context_result['prayer_info']}")
            
            if context_result['camera_specific_events']:
                logger.info(f"📅 Camera-specific events: {', '.join(context_result['camera_specific_events'])}")
            
            return {
                "status": "updated",
                "camera_id": camera_id,
                "camera_country": context_result['camera_country'],
                "context_result": context_result,
                "original_thresholds": original_thresholds,
                "new_thresholds": {
                    "crowd_density_threshold": self.crowd_density_threshold,
                    "gathering_size_threshold": self.gathering_size_threshold,
                    "max_normal_density": self.max_normal_density
                },
                "reasoning": self.context_reasoning,
                "camera_specific_events": context_result['camera_specific_events']
            }
            
        except Exception as e:
            logger.error(f"Error updating camera-specific thresholds for {camera_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "camera_id": camera_id,
                "thresholds": {
                    "crowd_density_threshold": self.crowd_density_threshold,
                    "gathering_size_threshold": self.gathering_size_threshold,
                    "max_normal_density": self.max_normal_density
                }
            }
    
    def get_current_threshold_info(self) -> Dict:
        """Get current threshold information with context"""
        return {
            "current_thresholds": {
                "crowd_density_threshold": self.crowd_density_threshold,
                "gathering_size_threshold": self.gathering_size_threshold,
                "max_normal_density": self.max_normal_density
            },
            "base_thresholds": {
                "crowd_density_threshold": self.base_crowd_density_threshold,
                "gathering_size_threshold": self.base_gathering_size_threshold,
                "max_normal_density": self.base_max_normal_density
            },
            "last_update": self.last_context_update.isoformat() if self.last_context_update else None,
            "context_reasoning": self.context_reasoning,
            "is_dynamic": dynamic_context_agent is not None
        }

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