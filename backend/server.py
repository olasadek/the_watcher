from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import motor.motor_asyncio
import os
from datetime import datetime
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
                elif isinstance(value, dict):
                    cleaned[key] = self._clean_dict_for_json(value)
                elif isinstance(value, list):
                    cleaned[key] = [self._clean_dict_for_json(item) if isinstance(item, dict) else item for item in value]
                else:
                    cleaned[key] = value
            return cleaned
        return data

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)