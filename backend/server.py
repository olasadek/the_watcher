from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import motor.motor_asyncio
import os
from datetime import datetime, timedelta
import uuid
import json
import asyncio
from typing import List, Dict, Optional
import math
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="The Watcher - University Monitoring System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.university_monitoring

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.booth_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, booth_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if booth_id:
            self.booth_connections[booth_id] = websocket

    def disconnect(self, websocket: WebSocket, booth_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if booth_id and booth_id in self.booth_connections:
            del self.booth_connections[booth_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def notify_closest_booth(self, incident_location: Dict, alert_data: Dict):
        closest_booth = await self.find_closest_booth(incident_location)
        if closest_booth and closest_booth['booth_id'] in self.booth_connections:
            websocket = self.booth_connections[closest_booth['booth_id']]
            
            # Convert ObjectId to string if present
            alert_data_clean = self._clean_dict_for_json(alert_data)
            
            alert_message = {
                "type": "PRIORITY_ALERT",
                "incident": alert_data_clean,
                "distance": closest_booth['distance'],
                "booth_info": closest_booth,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(alert_message))

    def _clean_dict_for_json(self, data):
        """Clean dictionary for JSON serialization"""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if key == '_id':  # Skip MongoDB ObjectId
                    continue
                elif isinstance(value, datetime):
                    cleaned[key] = value.isoformat()
                elif hasattr(value, '__dict__'):  # Handle objects with __dict__
                    try:
                        cleaned[key] = self._clean_dict_for_json(vars(value))
                    except TypeError:
                        # If vars() fails, convert to string
                        cleaned[key] = str(value)
                elif isinstance(value, dict):
                    cleaned[key] = self._clean_dict_for_json(value)
                elif isinstance(value, list):
                    cleaned[key] = [self._clean_dict_for_json(item) if isinstance(item, dict) else str(item) if hasattr(item, '__dict__') else item for item in value]
                else:
                    try:
                        # Test if the value is JSON serializable
                        import json
                        json.dumps(value)
                        cleaned[key] = value
                    except (TypeError, ValueError):
                        # If not serializable, convert to string
                        cleaned[key] = str(value)
            return cleaned
        elif isinstance(data, list):
            return [self._clean_dict_for_json(item) if isinstance(item, dict) else str(item) if hasattr(item, '__dict__') else item for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            try:
                return self._clean_dict_for_json(vars(data))
            except TypeError:
                return str(data)
        else:
            try:
                # Test if the value is JSON serializable
                import json
                json.dumps(data)
                return data
            except (TypeError, ValueError):
                return str(data)

    async def find_closest_booth(self, incident_location: Dict):
        booths = await db.security_booths.find({"status": "active"}).to_list(length=None)
        if not booths:
            return None
        
        min_distance = float('inf')
        closest_booth = None
        
        for booth in booths:
            distance = self.calculate_distance(
                incident_location['lat'], incident_location['lng'],
                booth['location']['lat'], booth['location']['lng']
            )
            if distance < min_distance:
                min_distance = distance
                closest_booth = {
                    "booth_id": booth['booth_id'],
                    "name": booth['name'],
                    "location": booth['location'],
                    "distance": round(distance, 2)
                }
        
        return closest_booth

    def calculate_distance(self, lat1, lng1, lat2, lng2):
        # Haversine formula for distance calculation
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlng/2) * math.sin(dlng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c * 1000  # Convert to meters
        
        return distance

manager = ConnectionManager()

# Pydantic models
class Camera(BaseModel):
    camera_id: str
    name: str
    location: Dict[str, float]  # lat, lng
    status: str = "active"
    feed_url: Optional[str] = None

class SecurityBooth(BaseModel):
    booth_id: str
    name: str
    location: Dict[str, float]  # lat, lng
    personnel: List[str]
    status: str = "active"

class Incident(BaseModel):
    incident_id: str
    camera_id: str
    incident_type: str
    severity: str
    location: Dict[str, float]
    timestamp: datetime
    description: str
    status: str = "active"
    assigned_booth: Optional[str] = None

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except:
        manager.disconnect(websocket)

@app.websocket("/ws/booth/{booth_id}")
async def booth_websocket(websocket: WebSocket, booth_id: str):
    await manager.connect(websocket, booth_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle booth-specific messages
            await manager.send_personal_message(f"Booth {booth_id} connected", websocket)
    except:
        manager.disconnect(websocket, booth_id)

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "The Watcher Monitoring System"}

@app.get("/api/cameras")
async def get_cameras():
    cameras = await db.cameras.find().to_list(length=None)
    # Clean ObjectId fields for JSON serialization
    cleaned_cameras = [manager._clean_dict_for_json(camera) for camera in cameras]
    return {"cameras": cleaned_cameras}

@app.post("/api/cameras")
async def create_camera(camera: Camera):
    camera_dict = camera.dict()
    camera_dict["created_at"] = datetime.utcnow()
    result = await db.cameras.insert_one(camera_dict)
    return {"message": "Camera created", "camera_id": camera.camera_id}

@app.get("/api/security-booths")
async def get_security_booths():
    booths = await db.security_booths.find().to_list(length=None)
    # Clean ObjectId fields for JSON serialization
    cleaned_booths = [manager._clean_dict_for_json(booth) for booth in booths]
    return {"booths": cleaned_booths}

@app.post("/api/security-booths")
async def create_security_booth(booth: SecurityBooth):
    booth_dict = booth.dict()
    booth_dict["created_at"] = datetime.utcnow()
    result = await db.security_booths.insert_one(booth_dict)
    return {"message": "Security booth created", "booth_id": booth.booth_id}

@app.get("/api/incidents")
async def get_incidents():
    incidents = await db.incidents.find().sort("timestamp", -1).to_list(length=50)
    # Clean ObjectId fields for JSON serialization
    cleaned_incidents = [manager._clean_dict_for_json(incident) for incident in incidents]
    return {"incidents": cleaned_incidents}

@app.post("/api/incidents")
async def create_incident(incident: Incident):
    incident_dict = incident.dict()
    incident_dict["created_at"] = datetime.utcnow()
    
    # Store incident
    result = await db.incidents.insert_one(incident_dict)
    
    # Notify closest security booth
    await manager.notify_closest_booth(incident.location, incident_dict)
    
    # Broadcast to all connected clients
    alert_data_clean = manager._clean_dict_for_json(incident_dict)
    await manager.broadcast(json.dumps({
        "type": "NEW_INCIDENT",
        "incident": alert_data_clean
    }))
    
    return {"message": "Incident created and alerts sent", "incident_id": incident.incident_id}

@app.post("/api/analyze-frame")
async def analyze_frame(file: UploadFile = File(...)):
    """
    Analyze uploaded frame for incidents using free computer vision
    """
    try:
        # Import vision analyzer
        from vision_analyzer import analyze_image_data
        
        # Read image data
        image_data = await file.read()
        
        # Analyze with computer vision
        analysis_results = analyze_image_data(image_data)
        
        if "error" in analysis_results:
            return {"error": analysis_results["error"]}
        
        # Process detected incidents
        incidents_detected = analysis_results.get("incidents_detected", [])
        
        created_incidents = []
        for incident in incidents_detected:
            # Only process high-confidence incidents
            if incident.get("confidence", 0) > 0.6:
                incident_id = str(uuid.uuid4())
                incident_data = {
                    "incident_id": incident_id,
                    "camera_id": "camera_webcam",  # Webcam feed
                    "incident_type": incident["type"],
                    "severity": incident.get("severity", "medium"),
                    "location": {"lat": 40.7128, "lng": -74.0060},  # Default location
                    "timestamp": datetime.utcnow(),
                    "description": f"AI detected {incident['type'].replace('_', ' ')} with {incident['confidence']:.2f} confidence",
                    "confidence": incident["confidence"],
                    "analysis_details": analysis_results.get("analysis_details", {})
                }
                
                # Store incident
                await db.incidents.insert_one(incident_data)
                created_incidents.append(incident_data)
                
                # Send alerts
                await manager.notify_closest_booth(incident_data["location"], incident_data)
                
                incident_data_clean = manager._clean_dict_for_json(incident_data)
                await manager.broadcast(json.dumps({
                    "type": "NEW_INCIDENT",
                    "incident": incident_data_clean
                }))
        
        return {
            "incidents_detected": len(created_incidents) > 0,
            "incidents_created": len(created_incidents),
            "analysis_results": analysis_results,
            "created_incidents": created_incidents
        }
        
    except Exception as e:
        logger.error(f"Frame analysis error: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}

@app.post("/api/simulate-incident")
async def simulate_incident():
    """
    Simulate an incident for testing purposes
    """
    import random
    
    incident_types = ["person_fallen", "fight", "smoking", "suspicious_activity"]
    incident_type = random.choice(incident_types)
    
    incident_id = str(uuid.uuid4())
    current_time = datetime.utcnow()
    incident_data = {
        "incident_id": incident_id,
        "camera_id": random.choice(["camera_001", "camera_002"]),
        "incident_type": incident_type,
        "severity": "high" if incident_type in ["person_fallen", "fight"] else "medium",
        "location": {
            "lat": 40.7128 + random.uniform(-0.005, 0.005), 
            "lng": -74.0060 + random.uniform(-0.005, 0.005)
        },
        "timestamp": current_time,
        "description": f"Simulated {incident_type.replace('_', ' ')} incident for testing",
        "confidence": random.uniform(0.7, 0.95),
        "status": "active"
    }
    
    # Store incident
    await db.incidents.insert_one(incident_data)
    
    # Convert datetime to string for JSON serialization
    incident_data_json = incident_data.copy()
    incident_data_json["timestamp"] = current_time.isoformat()
    
    # Send alerts
    await manager.notify_closest_booth(incident_data["location"], incident_data_json)
    
    alert_data_clean = manager._clean_dict_for_json(incident_data_json)
    await manager.broadcast(json.dumps({
        "type": "NEW_INCIDENT",
        "incident": alert_data_clean
    }))
    
    return {
        "message": "Incident simulated successfully",
        "incident": alert_data_clean
    }

@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    total_cameras = await db.cameras.count_documents({})
    active_incidents = await db.incidents.count_documents({"status": "active"})
    total_booths = await db.security_booths.count_documents({"status": "active"})
    
    recent_incidents = await db.incidents.find().sort("timestamp", -1).limit(5).to_list(length=5)
    # Clean ObjectId fields for JSON serialization
    cleaned_recent_incidents = [manager._clean_dict_for_json(incident) for incident in recent_incidents]
    
    return {
        "total_cameras": total_cameras,
        "active_incidents": active_incidents,
        "total_booths": total_booths,
        "recent_incidents": cleaned_recent_incidents
    }

@app.get("/api/crowd-stats")
async def get_crowd_statistics():
    """
    Get comprehensive crowd analysis statistics
    """
    try:
        from vision_analyzer import analyzer
        
        # Get crowd statistics from the analyzer
        crowd_stats = analyzer.get_crowd_statistics()
        
        # Get crowd-related incidents from database
        crowd_incidents = await db.incidents.find({
            "incident_type": {"$in": ["high_crowd_density", "unusual_gathering"]}
        }).sort("timestamp", -1).limit(10).to_list(length=10)
        
        cleaned_crowd_incidents = [manager._clean_dict_for_json(incident) for incident in crowd_incidents]
        
        # Calculate crowd trends (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_crowd_incidents = await db.incidents.count_documents({
            "incident_type": {"$in": ["high_crowd_density", "unusual_gathering"]},
            "timestamp": {"$gte": yesterday}
        })
        
        return {
            "current_statistics": crowd_stats,
            "recent_crowd_incidents": cleaned_crowd_incidents,
            "incidents_last_24h": recent_crowd_incidents,
            "crowd_risk_zones": await get_crowd_risk_zones()
        }
        
    except Exception as e:
        logger.error(f"Error getting crowd statistics: {str(e)}")
        return {"error": str(e)}

async def get_crowd_risk_zones():
    """
    Identify areas with high crowd-related incident frequency
    """
    try:
        # Aggregate incidents by location (simplified)
        pipeline = [
            {
                "$match": {
                    "incident_type": {"$in": ["high_crowd_density", "unusual_gathering"]},
                    "timestamp": {"$gte": datetime.utcnow() - timedelta(days=7)}
                }
            },
            {
                "$group": {
                    "_id": "$camera_id",
                    "incident_count": {"$sum": 1},
                    "avg_severity": {"$avg": {"$cond": [
                        {"$eq": ["$severity", "high"]}, 3,
                        {"$cond": [{"$eq": ["$severity", "medium"]}, 2, 1]}
                    ]}}
                }
            },
            {
                "$sort": {"incident_count": -1}
            },
            {
                "$limit": 5
            }
        ]
        
        risk_zones = await db.incidents.aggregate(pipeline).to_list(length=5)
        
        # Clean and format the results
        cleaned_zones = []
        for zone in risk_zones:
            cleaned_zones.append({
                "camera_id": zone["_id"],
                "incident_count": zone["incident_count"],
                "risk_level": "high" if zone["avg_severity"] > 2.5 else "medium" if zone["avg_severity"] > 1.5 else "low"
            })
        
        return cleaned_zones
        
    except Exception as e:
        logger.error(f"Error calculating risk zones: {str(e)}")
        return []

@app.post("/api/configure-crowd-thresholds")
async def configure_crowd_thresholds(
    max_density: float = 10.0,
    gathering_size: int = 8,
    gathering_duration: int = 30
):
    """
    Configure crowd analysis thresholds
    """
    try:
        from vision_analyzer import analyzer
        
        # Update analyzer thresholds
        analyzer.max_normal_density = max_density
        analyzer.gathering_size_threshold = gathering_size
        analyzer.gathering_duration_threshold = gathering_duration
        
        # Store configuration in database
        config_data = {
            "max_normal_density": max_density,
            "gathering_size_threshold": gathering_size,
            "gathering_duration_threshold": gathering_duration,
            "updated_at": datetime.utcnow()
        }
        
        await db.crowd_config.replace_one(
            {"type": "crowd_thresholds"},
            {"type": "crowd_thresholds", **config_data},
            upsert=True
        )
        
        return {
            "message": "Crowd analysis thresholds updated successfully",
            "configuration": config_data
        }
        
    except Exception as e:
        logger.error(f"Error configuring crowd thresholds: {str(e)}")
        return {"error": str(e)}

@app.get("/api/map-data")
async def get_map_data():
    """
    Get all map-related data (cameras, booths, incidents) in one request
    """
    try:
        cameras = await db.cameras.find().to_list(length=None)
        booths = await db.security_booths.find().to_list(length=None)
        recent_incidents = await db.incidents.find().sort("timestamp", -1).limit(20).to_list(length=20)
        
        # Clean ObjectId fields and handle serialization issues
        cleaned_cameras = []
        for camera in cameras:
            try:
                cleaned_cameras.append(manager._clean_dict_for_json(camera))
            except Exception as e:
                logger.warning(f"Error cleaning camera data: {e}")
                continue
        
        cleaned_booths = []
        for booth in booths:
            try:
                cleaned_booths.append(manager._clean_dict_for_json(booth))
            except Exception as e:
                logger.warning(f"Error cleaning booth data: {e}")
                continue
        
        cleaned_incidents = []
        for incident in recent_incidents:
            try:
                cleaned_incidents.append(manager._clean_dict_for_json(incident))
            except Exception as e:
                logger.warning(f"Error cleaning incident data: {e}")
                continue
        
        map_bounds = calculate_map_bounds(cleaned_cameras, cleaned_booths, cleaned_incidents)
        
        return {
            "cameras": cleaned_cameras,
            "security_booths": cleaned_booths,
            "incidents": cleaned_incidents,
            "map_bounds": map_bounds
        }
        
    except Exception as e:
        logger.error(f"Error getting map data: {str(e)}")
        return {
            "cameras": [],
            "security_booths": [],
            "incidents": [],
            "map_bounds": {
                "center": {"lat": 40.7128, "lng": -74.0060},
                "bounds": {"north": 40.7228, "south": 40.7028, "east": -74.0010, "west": -74.0110}
            },
            "error": str(e)
        }

def calculate_map_bounds(cameras, booths, incidents):
    """
    Calculate the bounding box for all map items
    """
    all_items = cameras + booths + incidents
    if not all_items:
        return {
            "center": {"lat": 40.7128, "lng": -74.0060},
            "bounds": {"north": 40.7228, "south": 40.7028, "east": -74.0010, "west": -74.0110}
        }
    
    lats = []
    lngs = []
    
    for item in all_items:
        location = item.get('location', {})
        if location and 'lat' in location and 'lng' in location:
            lats.append(location['lat'])
            lngs.append(location['lng'])
    
    if not lats or not lngs:
        return {
            "center": {"lat": 40.7128, "lng": -74.0060},
            "bounds": {"north": 40.7228, "south": 40.7028, "east": -74.0010, "west": -74.0110}
        }
    
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    
    # Add padding
    lat_padding = (max_lat - min_lat) * 0.1 or 0.01
    lng_padding = (max_lng - min_lng) * 0.1 or 0.01
    
    return {
        "center": {
            "lat": (min_lat + max_lat) / 2,
            "lng": (min_lng + max_lng) / 2
        },
        "bounds": {
            "north": max_lat + lat_padding,
            "south": min_lat - lat_padding,
            "east": max_lng + lng_padding,
            "west": min_lng - lng_padding
        }
    }

@app.get("/api/route/{incident_id}")
async def get_incident_route(incident_id: str):
    """
    Get the route from the closest security booth to an incident
    """
    try:
        # Get incident details
        incident = await db.incidents.find_one({"incident_id": incident_id})
        if not incident:
            return {"error": "Incident not found"}
        
        # Find closest booth
        closest_booth = await manager.find_closest_booth(incident['location'])
        if not closest_booth:
            return {"error": "No available security booths"}
        
        # Calculate simple route (straight line for now)
        incident_location = incident['location']
        booth_location = closest_booth['location']
        
        route = {
            "start": booth_location,
            "end": incident_location,
            "distance": closest_booth['distance'],
            "estimated_time": calculate_estimated_time(closest_booth['distance']),
            "waypoints": [booth_location, incident_location],  # Simple straight line
            "booth_info": closest_booth
        }
        
        return {"route": route}
        
    except Exception as e:
        logger.error(f"Error calculating route: {str(e)}")
        return {"error": str(e)}

def calculate_estimated_time(distance_meters):
    """
    Calculate estimated travel time (assuming walking speed of 5 km/h)
    """
    walking_speed_ms = 1.39  # meters per second (5 km/h)
    time_seconds = distance_meters / walking_speed_ms
    
    if time_seconds < 60:
        return f"{int(time_seconds)} seconds"
    elif time_seconds < 3600:
        return f"{int(time_seconds / 60)} minutes"
    else:
        return f"{int(time_seconds / 3600)} hours"

@app.post("/api/configure-university")
async def configure_university(config: dict):
    """Configure university with custom cameras and booths"""
    try:
        logger.info(f"Configuring university: {config.get('university')}")
        
        # Clear existing data
        await db.cameras.delete_many({})
        await db.security_booths.delete_many({})
        await db.incidents.delete_many({})
        
        # Store university configuration
        university_config = {
            "university_name": config.get("university"),
            "location": config.get("location"),
            "configured_at": datetime.utcnow()
        }
        await db.university_config.replace_one(
            {},  # Replace any existing config
            university_config,
            upsert=True
        )
        
        # Insert cameras
        cameras = config.get("cameras", [])
        for camera in cameras:
            camera["created_at"] = datetime.utcnow()
        
        if cameras:
            await db.cameras.insert_many(cameras)
        
        # Insert security booths
        booths = config.get("booths", [])
        for booth in booths:
            booth["created_at"] = datetime.utcnow()
            
        if booths:
            await db.security_booths.insert_many(booths)
        
        logger.info(f"Successfully configured {config.get('university')} with {len(cameras)} cameras and {len(booths)} booths")
        
        return {
            "message": f"University '{config.get('university')}' configured successfully!",
            "university": config.get("university"),
            "location": config.get("location"),
            "cameras_count": len(cameras),
            "booths_count": len(booths)
        }
        
    except Exception as e:
        logger.error(f"Error configuring university: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

@app.get("/api/university-config")
async def get_university_config():
    """Get current university configuration"""
    try:
        config = await db.university_config.find_one()
        if not config:
            return {
                "university_name": "No University Configured",
                "location": {"country": "Unknown", "city": "Unknown", "center": {"lat": 0, "lng": 0}},
                "configured_at": None
            }
        
        # Clean the config for JSON serialization
        config = _clean_dict_for_json(config)
        return config
        
    except Exception as e:
        logger.error(f"Error getting university config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@app.post("/api/reset-database")
async def reset_database():
    """Reset database and populate with AUB sample data"""
    try:
        logger.info("Resetting database with AUB data...")
        
        # Clear all collections
        await db.cameras.delete_many({})
        await db.security_booths.delete_many({})
        await db.incidents.delete_many({})
        logger.info("Cleared existing data")
        
        # Create AUB sample cameras
        sample_cameras = [
            {
                "camera_id": "cam_library_entrance",
                "name": "Jafet Library Main Entrance",
                "location": {"lat": 33.9008, "lng": 35.4822},  # AUB Jafet Library
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_student_center",
                "name": "Student Center Plaza",
                "location": {"lat": 33.9000, "lng": 35.4815},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_parking_lot_a",
                "name": "Parking Lot A",
                "location": {"lat": 33.8995, "lng": 35.4810},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_dining_hall",
                "name": "Dining Hall",
                "location": {"lat": 33.9012, "lng": 35.4828},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_gym_entrance",
                "name": "Gym Main Entrance",
                "location": {"lat": 33.8990, "lng": 35.4805},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_science_building",
                "name": "Science Building",
                "location": {"lat": 33.9015, "lng": 35.4830},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_dormitory_north",
                "name": "North Dormitory",
                "location": {"lat": 33.9020, "lng": 35.4825},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_administration",
                "name": "Administration Building",
                "location": {"lat": 33.9005, "lng": 35.4818},
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]

        # Create AUB sample security booths
        sample_booths = [
            {
                "booth_id": "booth_main_gate",
                "name": "Main Gate Security",
                "location": {"lat": 33.8998, "lng": 35.4818},
                "personnel": ["Officer Khalil", "Officer Maroun"],
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "booth_id": "booth_north_campus",
                "name": "North Campus Security",
                "location": {"lat": 33.9015, "lng": 35.4825},
                "personnel": ["Officer Fares"],
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "booth_id": "booth_south_campus",
                "name": "South Campus Security",
                "location": {"lat": 33.8985, "lng": 35.4810},
                "personnel": ["Officer Nadia", "Officer Ahmad"],
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "booth_id": "booth_central_plaza",
                "name": "Central Plaza Security",
                "location": {"lat": 33.9005, "lng": 35.4820},
                "personnel": ["Officer Layla", "Officer Omar"],
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]

        # Insert data
        camera_result = await db.cameras.insert_many(sample_cameras)
        booth_result = await db.security_booths.insert_many(sample_booths)
        
        logger.info(f"Created {len(sample_cameras)} AUB cameras and {len(sample_booths)} security booths")
        
        return {
            "message": "Database reset with AUB data successfully!",
            "cameras_created": len(sample_cameras),
            "booths_created": len(sample_booths)
        }
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")

@app.post("/api/cameras/bulk")
async def create_bulk_cameras():
    """
    Create sample cameras for testing the map
    """
    try:
        sample_cameras = [
            {
                "camera_id": "cam_library_entrance",
                "name": "Jafet Library Main Entrance",
                "location": {"lat": 33.9008, "lng": 35.4822},  # AUB Jafet Library
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_student_center",
                "name": "Student Center Plaza",
                "location": {"lat": 33.9000, "lng": 35.4815},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_parking_lot_a",
                "name": "Parking Lot A",
                "location": {"lat": 33.8995, "lng": 35.4810},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_dining_hall",
                "name": "Dining Hall",
                "location": {"lat": 33.9012, "lng": 35.4828},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_gym_entrance",
                "name": "Gym Main Entrance",
                "location": {"lat": 33.8990, "lng": 35.4805},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_science_building",
                "name": "Science Building",
                "location": {"lat": 33.9015, "lng": 35.4830},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_dormitory_north",
                "name": "North Dormitory",
                "location": {"lat": 33.9020, "lng": 35.4825},
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "camera_id": "cam_administration",
                "name": "Administration Building",
                "location": {"lat": 33.9005, "lng": 35.4818},
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]
        
        # Clear existing cameras first
        delete_result = await db.cameras.delete_many({})
        logger.info(f"Deleted {delete_result.deleted_count} existing cameras")
        
        # Insert new cameras
        result = await db.cameras.insert_many(sample_cameras)
        logger.info(f"Inserted {len(result.inserted_ids)} new cameras")
        
        # Return simple response without complex objects
        return {
            "message": f"Created {len(sample_cameras)} sample cameras",
            "count": len(sample_cameras),
            "camera_ids": [cam["camera_id"] for cam in sample_cameras]
        }
        
    except Exception as e:
        logger.error(f"Error creating bulk cameras: {str(e)}")
        return {"error": str(e), "message": "Failed to create sample cameras"}

@app.post("/api/security-booths/bulk")
async def create_bulk_security_booths():
    """
    Create sample security booths for testing the map
    """
    try:
        sample_booths = [
            {
                "booth_id": "booth_main_gate",
                "name": "Main Gate Security",
                "location": {"lat": 33.8998, "lng": 35.4818},
                "personnel": ["Officer Khalil", "Officer Maroun"],
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "booth_id": "booth_north_campus",
                "name": "North Campus Security",
                "location": {"lat": 33.9015, "lng": 35.4825},
                "personnel": ["Officer Fares"],
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "booth_id": "booth_south_campus",
                "name": "South Campus Security",
                "location": {"lat": 33.8985, "lng": 35.4810},
                "personnel": ["Officer Nadia", "Officer Ahmad"],
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "booth_id": "booth_central_plaza",
                "name": "Central Plaza Security",
                "location": {"lat": 33.9005, "lng": 35.4820},
                "personnel": ["Officer Layla", "Officer Omar"],
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]
        
        # Clear existing booths first
        delete_result = await db.security_booths.delete_many({})
        logger.info(f"Deleted {delete_result.deleted_count} existing security booths")
        
        # Insert new booths
        result = await db.security_booths.insert_many(sample_booths)
        logger.info(f"Inserted {len(result.inserted_ids)} new security booths")
        
        # Return simple response without complex objects
        return {
            "message": f"Created {len(sample_booths)} sample security booths",
            "count": len(sample_booths),
            "booth_ids": [booth["booth_id"] for booth in sample_booths]
        }
        
    except Exception as e:
        logger.error(f"Error creating bulk security booths: {str(e)}")
        return {"error": str(e), "message": "Failed to create sample security booths"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)