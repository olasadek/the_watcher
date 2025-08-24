import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';
import CrowdDashboard from './CrowdDashboard';
import InteractiveMap from './InteractiveMap';
import RealMap from './RealMap';
import UniversityConfig from './UniversityConfig';
import DynamicThresholds from './DynamicThresholds';
import { 
  Camera, 
  Shield, 
  AlertTriangle, 
  Users, 
  MapPin, 
  Volume2,
  Play,
  Pause,
  Settings,
  BarChart3,
  Navigation,
  Globe,
  School,
  Zap
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [cameras, setCameras] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [securityBooths, setSecurityBooths] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [websocket, setWebsocket] = useState(null);
  const [activeTab, setActiveTab] = useState('monitoring');
  const [universityConfig, setUniversityConfig] = useState(null); // New state for tab navigation
  
  const webcamRef = useRef(null);
  const audioRef = useRef(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const wsUrl = BACKEND_URL.replace('http', 'ws') + '/ws';
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWebsocket(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'NEW_INCIDENT') {
        setAlerts(prev => [...prev, data.incident]);
        playAlertSound();
      } else if (data.type === 'PRIORITY_ALERT') {
        setAlerts(prev => [...prev, { ...data.incident, priority: true, distance: data.distance }]);
        playPriorityAlertSound();
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Load initial data
  useEffect(() => {
    loadCameras();
    loadIncidents();
    loadSecurityBooths();
    loadDashboardStats();
    loadUniversityConfig();
  }, []);

  const loadUniversityConfig = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/university-config`);
      setUniversityConfig(response.data);
    } catch (error) {
      console.error('Error loading university config:', error);
    }
  };

  const loadCameras = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/cameras`);
      setCameras(response.data.cameras);
    } catch (error) {
      console.error('Error loading cameras:', error);
    }
  };

  const loadIncidents = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/incidents`);
      setIncidents(response.data.incidents);
    } catch (error) {
      console.error('Error loading incidents:', error);
    }
  };

  const loadSecurityBooths = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/security-booths`);
      setSecurityBooths(response.data.booths);
    } catch (error) {
      console.error('Error loading security booths:', error);
    }
  };

  const loadDashboardStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/dashboard-stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  };

  const playAlertSound = () => {
    // Create audio context for alert sound
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.5);
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.5);
  };

  const playPriorityAlertSound = () => {
    // More urgent sound for priority alerts
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Rapid beeping pattern
    for (let i = 0; i < 3; i++) {
      const startTime = audioContext.currentTime + (i * 0.3);
      oscillator.frequency.setValueAtTime(1000, startTime);
      gainNode.gain.setValueAtTime(0.5, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.2);
    }
    
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 1);
  };

  const captureAndAnalyze = async () => {
    if (!webcamRef.current) return;
    
    setIsAnalyzing(true);
    const imageSrc = webcamRef.current.getScreenshot();
    
    try {
      // Convert base64 to blob
      const response = await fetch(imageSrc);
      const blob = await response.blob();
      
      // Create form data
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');
      
      // Send to backend for analysis
      const analysisResponse = await axios.post(`${BACKEND_URL}/api/analyze-frame`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (analysisResponse.data.incident_detected) {
        // Refresh incidents and stats
        loadIncidents();
        loadDashboardStats();
      }
      
    } catch (error) {
      console.error('Error analyzing frame:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const addSampleCamera = async () => {
    const sampleCamera = {
      camera_id: `camera_${Date.now()}`,
      name: `Camera ${cameras.length + 1}`,
      location: { lat: 40.7128 + Math.random() * 0.01, lng: -74.0060 + Math.random() * 0.01 },
      status: "active"
    };
    
    try {
      await axios.post(`${BACKEND_URL}/api/cameras`, sampleCamera);
      loadCameras();
    } catch (error) {
      console.error('Error adding camera:', error);
    }
  };

  const addSampleSecurityBooth = async () => {
    const sampleBooth = {
      booth_id: `booth_${Date.now()}`,
      name: `Security Booth ${securityBooths.length + 1}`,
      location: { lat: 40.7128 + Math.random() * 0.02, lng: -74.0060 + Math.random() * 0.02 },
      personnel: [`Officer ${Math.floor(Math.random() * 100)}`],
      status: "active"
    };
    
    try {
      await axios.post(`${BACKEND_URL}/api/security-booths`, sampleBooth);
      loadSecurityBooths();
    } catch (error) {
      console.error('Error adding security booth:', error);
    }
  };

  const dismissAlert = (index) => {
    setAlerts(prev => prev.filter((_, i) => i !== index));
  };

  const simulateIncident = async () => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/simulate-incident`);
      console.log('Incident simulated:', response.data);
      // Refresh data
      loadIncidents();
      loadDashboardStats();
    } catch (error) {
      console.error('Error simulating incident:', error);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getIncidentIcon = (type) => {
    switch (type) {
      case 'person_fallen': return '🚨';
      case 'fight': return '⚔️';
      case 'smoking': return '🚭';
      case 'suspicious_activity': return '👁️';
      default: return '⚠️';
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-blue-400 mr-3" />
              <div>
                <h1 className="text-3xl font-bold text-white">
                  {universityConfig?.university_name || 'University Security System'}
                </h1>
                {universityConfig?.location && (
                  <p className="text-sm text-gray-300">
                    {universityConfig.location.city}, {universityConfig.location.country}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm">System Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Alert Bar */}
      {alerts.length > 0 && (
        <div className="bg-red-600 border-l-4 border-red-800">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Volume2 className="h-5 w-5 mr-2 animate-pulse" />
                <span className="font-semibold">ACTIVE ALERTS: {alerts.length}</span>
              </div>
              <div className="flex space-x-2">
                {alerts.slice(0, 3).map((alert, index) => (
                  <div key={index} className="flex items-center space-x-2 bg-red-700 px-3 py-1 rounded">
                    <span>{getIncidentIcon(alert.incident_type)}</span>
                    <span className="text-sm">{alert.incident_type?.replace('_', ' ')}</span>
                    {alert.priority && <span className="text-xs bg-red-800 px-1 rounded">PRIORITY</span>}
                    <button onClick={() => dismissAlert(index)} className="text-red-200 hover:text-white">×</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('monitoring')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'monitoring'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Security Monitoring
                </div>
              </button>
              <button
                onClick={() => setActiveTab('crowd')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'crowd'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Crowd Analysis
                </div>
              </button>
              <button
                onClick={() => setActiveTab('map')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'map'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Navigation className="w-4 h-4" />
                  Campus Map
                </div>
              </button>
              <button
                onClick={() => setActiveTab('realmap')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'realmap'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  Real Map (GPS)
                </div>
              </button>
              <button
                onClick={() => setActiveTab('config')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'config'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <School className="w-4 h-4" />
                  University Config
                </div>
              </button>
              <button
                onClick={() => setActiveTab('thresholds')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'thresholds'
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Dynamic Thresholds
                </div>
              </button>
            </nav>
          </div>
        </div>

        {/* Render Content Based on Active Tab */}
        {activeTab === 'monitoring' && (
          <>
            {/* Dashboard Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center">
              <Camera className="h-8 w-8 text-blue-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Active Cameras</p>
                <p className="text-2xl font-bold text-white">{dashboardStats.total_cameras || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Active Incidents</p>
                <p className="text-2xl font-bold text-white">{dashboardStats.active_incidents || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-green-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Security Booths</p>
                <p className="text-2xl font-bold text-white">{dashboardStats.total_booths || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-purple-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Personnel Online</p>
                <p className="text-2xl font-bold text-white">3</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Live Camera Feed */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Live Camera Feed</h2>
                <div className="flex space-x-2">
                  <button
                    onClick={captureAndAnalyze}
                    disabled={isAnalyzing}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded flex items-center space-x-2"
                  >
                    <Camera className="h-4 w-4" />
                    <span>{isAnalyzing ? 'Analyzing...' : 'Analyze Frame'}</span>
                  </button>
                  <button
                    onClick={simulateIncident}
                    className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded flex items-center space-x-2"
                  >
                    <AlertTriangle className="h-4 w-4" />
                    <span>Simulate Incident</span>
                  </button>
                </div>
              </div>
              
              <div className="bg-black rounded-lg overflow-hidden">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  className="w-full h-64 object-cover"
                />
              </div>
              
              <div className="mt-4 text-sm text-gray-400">
                <p>🔴 Live feed from computer camera</p>
                <p>🤖 AI analysis: Click "Analyze Frame" to detect incidents in real-time</p>
              </div>
            </div>

            {/* Camera Grid */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Camera Network</h2>
                <button
                  onClick={addSampleCamera}
                  className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm"
                >
                  + Add Camera
                </button>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {cameras.map((camera, index) => (
                  <div key={camera.camera_id} className="bg-gray-700 p-3 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{camera.name}</span>
                      <div className={`w-2 h-2 rounded-full ${camera.status === 'active' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                    </div>
                    <div className="bg-gray-900 h-20 rounded flex items-center justify-center">
                      <Camera className="h-6 w-6 text-gray-500" />
                    </div>
                    <div className="mt-2 text-xs text-gray-400 flex items-center">
                      <MapPin className="h-3 w-3 mr-1" />
                      {camera.location.lat.toFixed(4)}, {camera.location.lng.toFixed(4)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Recent Incidents */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <h2 className="text-xl font-bold mb-4">Recent Incidents</h2>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {incidents.slice(0, 10).map((incident, index) => (
                  <div key={incident.incident_id} className="bg-gray-700 p-3 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getIncidentIcon(incident.incident_type)}</span>
                        <span className="font-medium text-sm">{incident.incident_type?.replace('_', ' ')}</span>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(incident.severity)}`}>
                        {incident.severity}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mb-1">{incident.description}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(incident.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Security Booths */}
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Security Booths</h2>
                <button
                  onClick={addSampleSecurityBooth}
                  className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm"
                >
                  + Add Booth
                </button>
              </div>
              
              <div className="space-y-3">
                {securityBooths.map((booth, index) => (
                  <div key={booth.booth_id} className="bg-gray-700 p-3 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">{booth.name}</span>
                      <div className={`w-2 h-2 rounded-full ${booth.status === 'active' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                    </div>
                    <div className="text-xs text-gray-400 flex items-center mb-1">
                      <MapPin className="h-3 w-3 mr-1" />
                      {booth.location.lat.toFixed(4)}, {booth.location.lng.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-400">
                      Personnel: {booth.personnel?.join(', ') || 'None assigned'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        </>
        )}

        {/* Crowd Analysis Tab */}
        {activeTab === 'crowd' && (
          <CrowdDashboard />
        )}

        {/* Interactive Map Tab */}
        {activeTab === 'map' && (
          <InteractiveMap />
        )}

        {/* Real GPS Map Tab */}
        {activeTab === 'realmap' && (
          <RealMap />
        )}

        {/* University Configuration Tab */}
        {activeTab === 'config' && (
          <UniversityConfig />
        )}

        {/* Dynamic Thresholds Tab */}
        {activeTab === 'thresholds' && (
          <DynamicThresholds />
        )}
      </div>
    </div>
  );
}

export default App;