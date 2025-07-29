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
from pydantic import BaseModel

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
            alert_message = {
                "type": "PRIORITY_ALERT",
                "incident": alert_data,
                "distance": closest_booth['distance'],
                "booth_info": closest_booth,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(alert_message))

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
    return {"cameras": cameras}

@app.post("/api/cameras")
async def create_camera(camera: Camera):
    camera_dict = camera.dict()
    camera_dict["created_at"] = datetime.utcnow()
    result = await db.cameras.insert_one(camera_dict)
    return {"message": "Camera created", "camera_id": camera.camera_id}

@app.get("/api/security-booths")
async def get_security_booths():
    booths = await db.security_booths.find().to_list(length=None)
    return {"booths": booths}

@app.post("/api/security-booths")
async def create_security_booth(booth: SecurityBooth):
    booth_dict = booth.dict()
    booth_dict["created_at"] = datetime.utcnow()
    result = await db.security_booths.insert_one(booth_dict)
    return {"message": "Security booth created", "booth_id": booth.booth_id}

@app.get("/api/incidents")
async def get_incidents():
    incidents = await db.incidents.find().sort("timestamp", -1).to_list(length=50)
    return {"incidents": incidents}

@app.post("/api/incidents")
async def create_incident(incident: Incident):
    incident_dict = incident.dict()
    incident_dict["created_at"] = datetime.utcnow()
    
    # Store incident
    result = await db.incidents.insert_one(incident_dict)
    
    # Notify closest security booth
    await manager.notify_closest_booth(incident.location, incident_dict)
    
    # Broadcast to all connected clients
    await manager.broadcast(json.dumps({
        "type": "NEW_INCIDENT",
        "incident": incident_dict
    }))
    
    return {"message": "Incident created and alerts sent", "incident_id": incident.incident_id}

@app.post("/api/analyze-frame")
async def analyze_frame(file: UploadFile = File(...)):
    """
    Analyze uploaded frame for incidents using free computer vision
    This is a placeholder - will implement actual CV detection
    """
    # For now, simulate incident detection
    import random
    
    incident_types = ["normal", "person_fallen", "fight", "smoking", "suspicious_activity"]
    detected_type = random.choice(incident_types)
    confidence = random.uniform(0.3, 0.95)
    
    # If high confidence incident detected
    if detected_type != "normal" and confidence > 0.7:
        incident_id = str(uuid.uuid4())
        incident_data = {
            "incident_id": incident_id,
            "camera_id": "camera_001",  # Default for testing
            "incident_type": detected_type,
            "severity": "high" if detected_type in ["person_fallen", "fight"] else "medium",
            "location": {"lat": 40.7128, "lng": -74.0060},  # Default NYC coords
            "timestamp": datetime.utcnow(),
            "description": f"Detected {detected_type.replace('_', ' ')} with {confidence:.2f} confidence",
            "confidence": confidence
        }
        
        # Store incident
        await db.incidents.insert_one(incident_data)
        
        # Send alerts
        await manager.notify_closest_booth(incident_data["location"], incident_data)
        await manager.broadcast(json.dumps({
            "type": "NEW_INCIDENT",
            "incident": incident_data
        }))
        
        return {
            "incident_detected": True,
            "incident_type": detected_type,
            "confidence": confidence,
            "incident_id": incident_id
        }
    
    return {
        "incident_detected": False,
        "detected_type": detected_type,
        "confidence": confidence
    }

@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    total_cameras = await db.cameras.count_documents({})
    active_incidents = await db.incidents.count_documents({"status": "active"})
    total_booths = await db.security_booths.count_documents({"status": "active"})
    
    recent_incidents = await db.incidents.find().sort("timestamp", -1).limit(5).to_list(length=5)
    
    return {
        "total_cameras": total_cameras,
        "active_incidents": active_incidents,
        "total_booths": total_booths,
        "recent_incidents": recent_incidents
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)