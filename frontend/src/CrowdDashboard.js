import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Users, 
  AlertTriangle, 
  TrendingUp, 
  Clock,
  MapPin,
  Settings,
  BarChart3
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function CrowdDashboard() {
  const [crowdStats, setCrowdStats] = useState({});
  const [crowdIncidents, setCrowdIncidents] = useState([]);
  const [riskZones, setRiskZones] = useState([]);
  const [thresholds, setThresholds] = useState({
    maxDensity: 10.0,
    gatheringSize: 8,
    gatheringDuration: 30
  });
  const [loading, setLoading] = useState(true);
  const [showConfig, setShowConfig] = useState(false);

  useEffect(() => {
    loadCrowdData();
    const interval = setInterval(loadCrowdData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadCrowdData = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/crowd-stats`);
      const data = response.data;
      
      setCrowdStats(data.current_statistics || {});
      setCrowdIncidents(data.recent_crowd_incidents || []);
      setRiskZones(data.crowd_risk_zones || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading crowd data:', error);
      setLoading(false);
    }
  };

  const updateThresholds = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/configure-crowd-thresholds`, {
        max_density: thresholds.maxDensity,
        gathering_size: thresholds.gatheringSize,
        gathering_duration: thresholds.gatheringDuration
      });
      alert('Crowd thresholds updated successfully!');
      setShowConfig(false);
    } catch (error) {
      console.error('Error updating thresholds:', error);
      alert('Failed to update thresholds');
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-500 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-500 bg-gray-100';
    }
  };

  const getStabilityColor = (stability) => {
    switch (stability) {
      case 'stable': return 'text-green-600';
      case 'moderate': return 'text-yellow-600';
      case 'dynamic': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Users className="w-8 h-8" />
          Crowd Analysis Dashboard
        </h2>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Settings className="w-5 h-5" />
          Configure
        </button>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Crowd Analysis Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Max Normal Density
              </label>
              <input
                type="number"
                step="0.1"
                value={thresholds.maxDensity}
                onChange={(e) => setThresholds({...thresholds, maxDensity: parseFloat(e.target.value)})}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Gathering Size Threshold
              </label>
              <input
                type="number"
                value={thresholds.gatheringSize}
                onChange={(e) => setThresholds({...thresholds, gatheringSize: parseInt(e.target.value)})}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Gathering Duration (seconds)
              </label>
              <input
                type="number"
                value={thresholds.gatheringDuration}
                onChange={(e) => setThresholds({...thresholds, gatheringDuration: parseInt(e.target.value)})}
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={updateThresholds}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
            >
              Update Settings
            </button>
            <button
              onClick={() => setShowConfig(false)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Current Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Current Crowd Size</p>
              <p className="text-2xl font-bold text-white">{crowdStats.current_crowd_size || 0}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Max Crowd Seen</p>
              <p className="text-2xl font-bold text-white">{crowdStats.max_crowd_size || 0}</p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Average Density</p>
              <p className="text-2xl font-bold text-white">{crowdStats.avg_density || 0}</p>
            </div>
            <BarChart3 className="w-10 h-10 text-yellow-500" />
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Observations</p>
              <p className="text-2xl font-bold text-white">{crowdStats.total_observations || 0}</p>
            </div>
            <Clock className="w-10 h-10 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Risk Zones */}
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MapPin className="w-5 h-5" />
          High-Risk Crowd Zones
        </h3>
        <div className="space-y-3">
          {riskZones.length > 0 ? (
            riskZones.map((zone, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-700 p-4 rounded-lg">
                <div>
                  <p className="text-white font-medium">{zone.camera_id}</p>
                  <p className="text-gray-400 text-sm">{zone.incident_count} incidents this week</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(zone.risk_level)}`}>
                  {zone.risk_level.toUpperCase()}
                </span>
              </div>
            ))
          ) : (
            <p className="text-gray-400">No high-risk zones identified</p>
          )}
        </div>
      </div>

      {/* Recent Crowd Incidents */}
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Recent Crowd Incidents
        </h3>
        <div className="space-y-3">
          {crowdIncidents.length > 0 ? (
            crowdIncidents.map((incident, index) => (
              <div key={index} className="bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskLevelColor(incident.severity)}`}>
                      {incident.severity.toUpperCase()}
                    </span>
                    <span className="text-white font-medium">
                      {incident.incident_type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <span className="text-gray-400 text-sm">
                    {new Date(incident.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-300 text-sm">{incident.description}</p>
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-400">
                  <span>Camera: {incident.camera_id}</span>
                  {incident.confidence && (
                    <span>Confidence: {(incident.confidence * 100).toFixed(1)}%</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-400">No recent crowd incidents</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default CrowdDashboard;
