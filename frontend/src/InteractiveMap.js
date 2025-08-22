import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  MapPin, 
  Camera, 
  Shield, 
  AlertTriangle,
  Navigation,
  Layers,
  Filter,
  RefreshCw,
  ZoomIn,
  ZoomOut
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Simple map implementation without external dependencies
function InteractiveMap() {
  const [cameras, setCameras] = useState([]);
  const [securityBooths, setSecurityBooths] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [mapCenter, setMapCenter] = useState({ lat: 40.7128, lng: -74.0060 }); // Default to NYC
  const [zoom, setZoom] = useState(15);
  const [showLayers, setShowLayers] = useState({
    cameras: true,
    booths: true,
    incidents: true,
    routes: false
  });
  const [loading, setLoading] = useState(true);
  const mapRef = useRef(null);

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
      
      // Auto-fit map if we have bounds
      if (data.map_bounds && data.map_bounds.center) {
        setMapCenter(data.map_bounds.center);
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
      
      // Create sample cameras and booths
      await Promise.all([
        axios.post(`${BACKEND_URL}/api/cameras/bulk`),
        axios.post(`${BACKEND_URL}/api/security-booths/bulk`)
      ]);
      
      // Reload map data
      await loadMapData();
      
      alert('Sample campus data created successfully!');
    } catch (error) {
      console.error('Error creating sample data:', error);
      alert('Failed to create sample data');
      setLoading(false);
    }
  };

  const calculateMapBounds = () => {
    const allItems = [...cameras, ...securityBooths, ...incidents];
    if (allItems.length === 0) return null;

    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;

    allItems.forEach(item => {
      const lat = item.location?.lat || item.lat || 0;
      const lng = item.location?.lng || item.lng || 0;
      
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    });

    return {
      center: {
        lat: (minLat + maxLat) / 2,
        lng: (minLng + maxLng) / 2
      },
      bounds: { minLat, maxLat, minLng, maxLng }
    };
  };

  const fitMapToBounds = () => {
    const bounds = calculateMapBounds();
    if (bounds) {
      setMapCenter(bounds.center);
      // Calculate appropriate zoom level based on bounds
      const latDiff = bounds.bounds.maxLat - bounds.bounds.minLat;
      const lngDiff = bounds.bounds.maxLng - bounds.bounds.minLng;
      const maxDiff = Math.max(latDiff, lngDiff);
      
      let newZoom = 15;
      if (maxDiff > 0.1) newZoom = 10;
      else if (maxDiff > 0.05) newZoom = 12;
      else if (maxDiff > 0.01) newZoom = 14;
      
      setZoom(newZoom);
    }
  };

  const convertToPixels = (lat, lng) => {
    // Simple projection for demonstration (not suitable for large areas)
    const scale = Math.pow(2, zoom);
    const mapSize = 512; // Base map size
    
    const x = ((lng - mapCenter.lng) * scale * 100000 + mapSize / 2);
    const y = ((mapCenter.lat - lat) * scale * 100000 + mapSize / 2);
    
    return { x, y };
  };

  const handleMapClick = (event) => {
    const rect = mapRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Convert click position back to lat/lng (simplified)
    const scale = Math.pow(2, zoom);
    const mapSize = 512;
    
    const lng = ((x - mapSize / 2) / (scale * 100000)) + mapCenter.lng;
    const lat = mapCenter.lat - ((y - mapSize / 2) / (scale * 100000));
    
    console.log('Clicked at:', { lat, lng });
    setSelectedItem(null);
  };

  const getIncidentColor = (incident) => {
    if (incident.severity === 'high') return 'bg-red-500';
    if (incident.severity === 'medium') return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const getIncidentAge = (timestamp) => {
    const now = new Date();
    const incidentTime = new Date(timestamp);
    const diffMinutes = Math.floor((now - incidentTime) / (1000 * 60));
    
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return `${Math.floor(diffMinutes / 1440)}d ago`;
  };

  const renderMapItem = (item, type, index) => {
    const lat = item.location?.lat || item.lat || 0;
    const lng = item.location?.lng || item.lng || 0;
    const position = convertToPixels(lat, lng);
    
    // Don't render items outside visible area
    if (position.x < -50 || position.x > 562 || position.y < -50 || position.y > 562) {
      return null;
    }

    const isSelected = selectedItem?.id === (item.camera_id || item.booth_id || item.incident_id);

    let icon, bgColor, borderColor;
    switch (type) {
      case 'camera':
        icon = <Camera className="w-3 h-3" />;
        bgColor = item.status === 'active' ? 'bg-blue-600' : 'bg-gray-600';
        borderColor = 'border-blue-300';
        break;
      case 'booth':
        icon = <Shield className="w-3 h-3" />;
        bgColor = item.status === 'active' ? 'bg-green-600' : 'bg-gray-600';
        borderColor = 'border-green-300';
        break;
      case 'incident':
        icon = <AlertTriangle className="w-3 h-3" />;
        bgColor = getIncidentColor(item);
        borderColor = 'border-red-300';
        break;
      default:
        return null;
    }

    return (
      <div
        key={`${type}-${index}`}
        className={`absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-200 ${
          isSelected ? 'scale-150 z-20' : 'z-10 hover:scale-125'
        }`}
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }}
        onClick={(e) => {
          e.stopPropagation();
          setSelectedItem({
            ...item,
            type,
            id: item.camera_id || item.booth_id || item.incident_id
          });
        }}
      >
        <div className={`w-6 h-6 rounded-full ${bgColor} ${borderColor} border-2 flex items-center justify-center text-white shadow-lg`}>
          {icon}
        </div>
        {type === 'incident' && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
        )}
      </div>
    );
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
          Campus Security Map
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={createSampleData}
            className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg flex items-center gap-2"
            disabled={loading}
          >
            <MapPin className="w-4 h-4" />
            Create Sample Data
          </button>
          <button
            onClick={fitMapToBounds}
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg flex items-center gap-2"
          >
            <Navigation className="w-4 h-4" />
            Fit to View
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

          {/* Zoom Controls */}
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">Zoom</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoom(Math.max(10, zoom - 1))}
                className="bg-gray-700 hover:bg-gray-600 text-white p-2 rounded"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-white text-sm flex-1 text-center">Level {zoom}</span>
              <button
                onClick={() => setZoom(Math.min(18, zoom + 1))}
                className="bg-gray-700 hover:bg-gray-600 text-white p-2 rounded"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Legend */}
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-3">Legend</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-600 rounded-full flex items-center justify-center">
                  <Camera className="w-2 h-2 text-white" />
                </div>
                <span className="text-gray-300">Camera</span>
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
            <div
              ref={mapRef}
              className="relative w-full h-96 bg-gray-700 cursor-move"
              onClick={handleMapClick}
              style={{
                backgroundImage: `
                  linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
                `,
                backgroundSize: '20px 20px'
              }}
            >
              {/* Grid overlay */}
              <div className="absolute inset-0 opacity-20">
                {/* Render grid lines */}
              </div>

              {/* Render map items */}
              {showLayers.cameras && cameras.map((camera, index) => 
                renderMapItem(camera, 'camera', index)
              )}
              
              {showLayers.booths && securityBooths.map((booth, index) => 
                renderMapItem(booth, 'booth', index)
              )}
              
              {showLayers.incidents && incidents.map((incident, index) => 
                renderMapItem(incident, 'incident', index)
              )}

              {/* Map center marker */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <div className="w-1 h-1 bg-white rounded-full opacity-50"></div>
              </div>
            </div>

            {/* Selected Item Details */}
            {selectedItem && (
              <div className="bg-gray-900 p-4 border-t border-gray-700">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-lg font-semibold text-white">
                      {selectedItem.name || selectedItem.incident_type?.replace('_', ' ') || 'Selected Item'}
                    </h4>
                    <p className="text-gray-400 text-sm capitalize">{selectedItem.type}</p>
                  </div>
                  <button
                    onClick={() => setSelectedItem(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    ×
                  </button>
                </div>
                
                <div className="mt-3 space-y-2 text-sm">
                  {selectedItem.type === 'camera' && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Status:</span>
                        <span className={selectedItem.status === 'active' ? 'text-green-400' : 'text-red-400'}>
                          {selectedItem.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Location:</span>
                        <span className="text-white">
                          {selectedItem.location?.lat?.toFixed(4)}, {selectedItem.location?.lng?.toFixed(4)}
                        </span>
                      </div>
                    </>
                  )}
                  
                  {selectedItem.type === 'booth' && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Status:</span>
                        <span className={selectedItem.status === 'active' ? 'text-green-400' : 'text-red-400'}>
                          {selectedItem.status}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Personnel:</span>
                        <span className="text-white">{selectedItem.personnel?.length || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Location:</span>
                        <span className="text-white">
                          {selectedItem.location?.lat?.toFixed(4)}, {selectedItem.location?.lng?.toFixed(4)}
                        </span>
                      </div>
                    </>
                  )}
                  
                  {selectedItem.type === 'incident' && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Severity:</span>
                        <span className={`${
                          selectedItem.severity === 'high' ? 'text-red-400' :
                          selectedItem.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                        }`}>
                          {selectedItem.severity}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Time:</span>
                        <span className="text-white">{getIncidentAge(selectedItem.timestamp)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Camera:</span>
                        <span className="text-white">{selectedItem.camera_id}</span>
                      </div>
                      {selectedItem.description && (
                        <div className="mt-2">
                          <span className="text-gray-400 block">Description:</span>
                          <span className="text-white text-xs">{selectedItem.description}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default InteractiveMap;
