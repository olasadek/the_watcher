import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  MapPin, 
  Camera, 
  Shield, 
  AlertTriangle,
  Navigation,
  Layers,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Route,
  Clock
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCAyNSA0MSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyLjUgMEMxOS40MDM2IDAgMjUgNS41OTY0NCAyNSAxMi41QzI1IDE5LjQwMzYgMTkuNDAzNiAyNSAxMi41IDI1QzUuNTk2NDQgMjUgMCAxOS40MDM2IDAgMTIuNUMwIDUuNTk2NDQgNS41OTY0NCAwIDEyLjUgMFoiIGZpbGw9IiMzQjgyRjYiLz4KPHBhdGggZD0iTTEyLjUgMzNMMCAyMFYxNEwxMi41IDQxTDI1IDE0VjIwTDEyLjUgMzNaIiBmaWxsPSIjMzM2N0Q2Ii8+Cjwvc3ZnPgo=',
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCAyNSA0MSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyLjUgMEMxOS40MDM2IDAgMjUgNS41OTY0NCAyNSAxMi41QzI1IDE5LjQwMzYgMTkuNDAzNiAyNSAxMi41IDI1QzUuNTk2NDQgMjUgMCAxOS40MDM2IDAgMTIuNUMwIDUuNTk2NDQgNS41OTY0NCAwIDEyLjUgMFoiIGZpbGw9IiMzQjgyRjYiLz4KPHBhdGggZD0iTTEyLjUgMzNMMCAyMFYxNEwxMi41IDQxTDI1IDE0VjIwTDEyLjUgMzNaIiBmaWxsPSIjMzM2N0Q2Ii8+Cjwvc3ZnPgo=',
  shadowUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDEiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCA0MSA0MSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGVsbGlwc2UgY3g9IjIwLjUiIGN5PSIyMC41IiByeD0iMjAuNSIgcnk9IjIwLjUiIGZpbGw9IiMwMDAwMDAiIGZpbGwtb3BhY2l0eT0iMC4zIi8+Cjwvc3ZnPgo=',
});

// Custom icons for different marker types
const createCustomIcon = (type, color) => {
  const svgIcon = `
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="15" cy="15" r="15" fill="${color}" stroke="white" stroke-width="2"/>
      <g transform="translate(7.5, 7.5)" fill="white">
        ${type === 'camera' ? 
          '<path d="M2 4h12v8H2z"/><circle cx="8" cy="8" r="2"/>' :
          type === 'booth' ? 
          '<path d="M8 1l6 4v10H2V5l6-4z"/><rect x="4" y="7" width="8" height="2"/>' :
          '<path d="M8 1l6 6H9l-1 7-1-7H2l6-6z"/>'
        }
      </g>
    </svg>
  `;
  
  return L.divIcon({
    html: svgIcon,
    className: 'custom-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15]
  });
};

// Component to fit map bounds
function MapBounds({ bounds }) {
  const map = useMap();
  
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [bounds, map]);
  
  return null;
}

function RealMap() {
  const [cameras, setCameras] = useState([]);
  const [securityBooths, setSecurityBooths] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showLayers, setShowLayers] = useState({
    cameras: true,
    booths: true,
    incidents: true,
    routes: false
  });
  const [loading, setLoading] = useState(true);
  const [mapBounds, setMapBounds] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const mapRef = useRef(null);

  // AUB campus center (American University of Beirut, Lebanon)
  const defaultCenter = [33.9002, 35.4818];

  useEffect(() => {
    loadMapData();
    const interval = setInterval(loadMapData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadMapData = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/map-data`);
      const data = response.data;
      
      setCameras(data.cameras || []);
      setSecurityBooths(data.security_booths || []);
      setIncidents(data.incidents || []);
      
      // Calculate bounds for all items
      const allItems = [...(data.cameras || []), ...(data.security_booths || []), ...(data.incidents || [])];
      if (allItems.length > 0) {
        const bounds = allItems
          .filter(item => item.location && item.location.lat && item.location.lng)
          .map(item => [item.location.lat, item.location.lng]);
        
        if (bounds.length > 0) {
          setMapBounds(bounds);
        }
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading map data:', error);
      setLoading(false);
    }
  };

  const createSampleData = async () => {
    try {
      setLoading(true);
      
      // Reset database with AUB data
      const response = await axios.post(`${BACKEND_URL}/api/reset-database`);
      console.log('Reset response:', response.data);
      
      // Reload map data
      await loadMapData();
      
      alert('AUB campus data reset successfully! 🎉');
    } catch (error) {
      console.error('Error resetting AUB data:', error);
      alert('Failed to reset AUB data. Please check the console for details.');
      setLoading(false);
    }
  };

  const getRouteToIncident = async (incidentId) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/route/${incidentId}`);
      setSelectedRoute(response.data.route);
    } catch (error) {
      console.error('Error getting route:', error);
    }
  };

  const getIncidentAge = (timestamp) => {
    const now = new Date();
    const incidentTime = new Date(timestamp);
    const diffMinutes = Math.floor((now - incidentTime) / (1000 * 60));
    
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return `${Math.floor(diffMinutes / 1440)}d ago`;
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  const renderMarkers = () => {
    const markers = [];

    // Camera markers
    if (showLayers.cameras) {
      cameras.forEach((camera, index) => {
        if (camera.location && camera.location.lat && camera.location.lng) {
          markers.push(
            <Marker
              key={`camera-${index}`}
              position={[camera.location.lat, camera.location.lng]}
              icon={createCustomIcon('camera', camera.status === 'active' ? '#3B82F6' : '#6B7280')}
            >
              <Popup>
                <div className="p-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Camera className="w-4 h-4 text-blue-600" />
                    <span className="font-semibold">{camera.name}</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div>Status: <span className={camera.status === 'active' ? 'text-green-600' : 'text-red-600'}>{camera.status}</span></div>
                    <div>ID: {camera.camera_id}</div>
                    <div>Location: {camera.location.lat.toFixed(4)}, {camera.location.lng.toFixed(4)}</div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        }
      });
    }

    // Security booth markers
    if (showLayers.booths) {
      securityBooths.forEach((booth, index) => {
        if (booth.location && booth.location.lat && booth.location.lng) {
          markers.push(
            <Marker
              key={`booth-${index}`}
              position={[booth.location.lat, booth.location.lng]}
              icon={createCustomIcon('booth', booth.status === 'active' ? '#10B981' : '#6B7280')}
            >
              <Popup>
                <div className="p-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-green-600" />
                    <span className="font-semibold">{booth.name}</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div>Status: <span className={booth.status === 'active' ? 'text-green-600' : 'text-red-600'}>{booth.status}</span></div>
                    <div>Personnel: {booth.personnel?.length || 0}</div>
                    <div>Officers: {booth.personnel?.join(', ') || 'None assigned'}</div>
                    <div>Location: {booth.location.lat.toFixed(4)}, {booth.location.lng.toFixed(4)}</div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        }
      });
    }

    // Incident markers
    if (showLayers.incidents) {
      incidents.forEach((incident, index) => {
        if (incident.location && incident.location.lat && incident.location.lng) {
          markers.push(
            <Marker
              key={`incident-${index}`}
              position={[incident.location.lat, incident.location.lng]}
              icon={createCustomIcon('incident', getSeverityColor(incident.severity))}
            >
              <Popup>
                <div className="p-2">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                    <span className="font-semibold">{incident.incident_type?.replace('_', ' ').toUpperCase()}</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div>Severity: <span style={{color: getSeverityColor(incident.severity)}}>{incident.severity}</span></div>
                    <div>Time: {getIncidentAge(incident.timestamp)}</div>
                    <div>Camera: {incident.camera_id}</div>
                    {incident.confidence && (
                      <div>Confidence: {(incident.confidence * 100).toFixed(1)}%</div>
                    )}
                    {incident.description && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
                        {incident.description}
                      </div>
                    )}
                    <button
                      onClick={() => getRouteToIncident(incident.incident_id)}
                      className="mt-2 bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700 flex items-center gap-1"
                    >
                      <Route className="w-3 h-3" />
                      Show Route
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        }
      });
    }

    return markers;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Navigation className="w-8 h-8" />
          AUB Campus Map - Beirut, Lebanon
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={createSampleData}
            className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg flex items-center gap-2"
            disabled={loading}
          >
            <MapPin className="w-4 h-4" />
            Reset to AUB Data
          </button>
          <button
            onClick={loadMapData}
            className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Map Controls */}
        <div className="lg:col-span-1 space-y-4">
          {/* Layer Controls */}
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Layers className="w-5 h-5" />
              Map Layers
            </h3>
            <div className="space-y-2">
              {Object.entries(showLayers).map(([layer, visible]) => (
                <label key={layer} className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={visible}
                    onChange={(e) => setShowLayers({...showLayers, [layer]: e.target.checked})}
                    className="rounded bg-gray-700 border-gray-600"
                  />
                  <span className="text-gray-300 capitalize">{layer}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Map Statistics */}
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">Statistics</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Cameras:</span>
                <span className="text-white">{cameras.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Security Booths:</span>
                <span className="text-white">{securityBooths.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Active Incidents:</span>
                <span className="text-red-400">{incidents.filter(i => i.status === 'active').length}</span>
              </div>
            </div>
          </div>

          {/* Route Information */}
          {selectedRoute && (
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <Route className="w-5 h-5" />
                Route Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Distance:</span>
                  <span className="text-white">{selectedRoute.distance}m</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">ETA:</span>
                  <span className="text-white">{selectedRoute.estimated_time}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Booth:</span>
                  <span className="text-white">{selectedRoute.booth_info?.name}</span>
                </div>
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">Legend</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-600 rounded-full flex items-center justify-center">
                  <Camera className="w-2 h-2 text-white" />
                </div>
                <span className="text-gray-300">Active Camera</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-green-600 rounded-full flex items-center justify-center">
                  <Shield className="w-2 h-2 text-white" />
                </div>
                <span className="text-gray-300">Security Booth</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                  <AlertTriangle className="w-2 h-2 text-white" />
                </div>
                <span className="text-gray-300">High Priority Incident</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center">
                  <AlertTriangle className="w-2 h-2 text-white" />
                </div>
                <span className="text-gray-300">Medium Priority Incident</span>
              </div>
            </div>
          </div>
        </div>

        {/* Map Container */}
        <div className="lg:col-span-3">
          <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
            <MapContainer
              center={defaultCenter}
              zoom={13}
              style={{ height: '600px', width: '100%' }}
              ref={mapRef}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              
              {mapBounds && <MapBounds bounds={mapBounds} />}
              
              {renderMarkers()}
            </MapContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RealMap;
