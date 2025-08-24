import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Users, MapPin, Settings, Bell, Globe, Moon, Sun, Camera } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const DynamicThresholds = () => {
  const [contextStatus, setContextStatus] = useState(null);
  const [thresholdInfo, setThresholdInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [camerasbyCountry, setCamerasByCountry] = useState({});
  const [newEvent, setNewEvent] = useState({
    event_type: 'religious_festival',
    description: '',
    start_time: '',
    end_time: '',
    crowd_multiplier: 2.0,
    target_countries: []
  });

  useEffect(() => {
    loadContextStatus();
    loadThresholdInfo();
    loadCamerasByCountry();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadContextStatus();
      loadThresholdInfo();
      loadCamerasByCountry();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadCamerasByCountry = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/cameras-by-country`);
      if (response.data.success) {
        setCamerasByCountry(response.data);
      }
    } catch (error) {
      console.error('Error loading cameras by country:', error);
    }
  };

  const loadContextStatus = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/context-status`);
      setContextStatus(response.data);
    } catch (error) {
      console.error('Error loading context status:', error);
      setError('Failed to load context status');
    }
  };

  const loadThresholdInfo = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/dynamic-thresholds`);
      setThresholdInfo(response.data);
    } catch (error) {
      console.error('Error loading threshold info:', error);
    }
  };

  const initializeLocationContext = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/initialize-location-context`);
      alert(response.data.message);
      loadContextStatus();
      loadThresholdInfo();
    } catch (error) {
      console.error('Error initializing context:', error);
      alert('Failed to initialize location context');
    } finally {
      setLoading(false);
    }
  };

  const simulatePrayerTime = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/simulate-prayer-time`);
      alert(`Prayer time simulation started: ${response.data.event.description}`);
      loadContextStatus();
      loadThresholdInfo();
    } catch (error) {
      console.error('Error simulating prayer time:', error);
      alert('Failed to simulate prayer time');
    } finally {
      setLoading(false);
    }
  };

  const addEvent = async () => {
    if (!newEvent.description || !newEvent.start_time || !newEvent.end_time) {
      alert('Please fill in all event details');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/add-event`, newEvent);
      alert(`Event added: ${response.data.event.description}`);
      
      // Reset form
      setNewEvent({
        event_type: 'religious_festival',
        description: '',
        start_time: '',
        end_time: '',
        crowd_multiplier: 2.0,
        target_countries: []
      });
      
      loadContextStatus();
      loadThresholdInfo();
    } catch (error) {
      console.error('Error adding event:', error);
      alert('Failed to add event');
    } finally {
      setLoading(false);
    }
  };

  const removeEvents = async (eventType) => {
    setLoading(true);
    try {
      const response = await axios.delete(`${BACKEND_URL}/api/remove-events/${eventType}`);
      alert(response.data.message);
      loadContextStatus();
      loadThresholdInfo();
    } catch (error) {
      console.error('Error removing events:', error);
      alert('Failed to remove events');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateTimeStr) => {
    return new Date(dateTimeStr).toLocaleString();
  };

  const getEventTypeIcon = (eventType) => {
    switch (eventType) {
      case 'prayer_time': return <Moon className="w-4 h-4 text-blue-400" />;
      case 'religious_festival': return <Calendar className="w-4 h-4 text-purple-400" />;
      case 'cultural_festival': return <Globe className="w-4 h-4 text-green-400" />;
      case 'academic_break': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'political_tension': return <Bell className="w-4 h-4 text-red-400" />;
      default: return <Calendar className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <Settings className="w-8 h-8 mr-3 text-blue-400" />
            Dynamic Adaptive Thresholds
          </h1>
          <p className="text-gray-400">
            AI-powered crowd thresholds that adapt to prayer times, cultural events, and population density
          </p>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Control Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Location Context */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <MapPin className="w-5 h-5 mr-2 text-green-400" />
              Location Context
            </h2>
            
            {contextStatus?.context_status?.location_context ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Country:</span>
                  <span className="font-semibold">{contextStatus.context_status.location_context.country}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">City:</span>
                  <span className="font-semibold">{contextStatus.context_status.location_context.city}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Population Density:</span>
                  <span className="font-semibold">{contextStatus.context_status.location_context.population_density}/km²</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Cultural Context:</span>
                  <span className="font-semibold capitalize">{contextStatus.context_status.location_context.cultural_context}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-400 mb-4">Location context not initialized</p>
                <button
                  onClick={initializeLocationContext}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded"
                >
                  {loading ? 'Initializing...' : 'Initialize Context'}
                </button>
              </div>
            )}
          </div>

          {/* Current Thresholds */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Users className="w-5 h-5 mr-2 text-orange-400" />
              Current Thresholds
            </h2>
            
            {thresholdInfo?.dynamic_thresholds ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Crowd Density:</span>
                  <span className="font-semibold">
                    {thresholdInfo.dynamic_thresholds.base_thresholds.crowd_density_threshold} → 
                    <span className="text-green-400 ml-1">
                      {thresholdInfo.dynamic_thresholds.current_thresholds.crowd_density_threshold}
                    </span>
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Gathering Size:</span>
                  <span className="font-semibold">
                    {thresholdInfo.dynamic_thresholds.base_thresholds.gathering_size_threshold} → 
                    <span className="text-green-400 ml-1">
                      {thresholdInfo.dynamic_thresholds.current_thresholds.gathering_size_threshold}
                    </span>
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Max Normal Density:</span>
                  <span className="font-semibold">
                    {thresholdInfo.dynamic_thresholds.base_thresholds.max_normal_density} → 
                    <span className="text-green-400 ml-1">
                      {thresholdInfo.dynamic_thresholds.current_thresholds.max_normal_density}
                    </span>
                  </span>
                </div>
                <div className="mt-4 pt-3 border-t border-gray-700">
                  <span className="text-sm text-gray-400">Last Updated:</span>
                  <p className="text-xs text-gray-300">
                    {thresholdInfo.dynamic_thresholds.last_update ? formatDateTime(thresholdInfo.dynamic_thresholds.last_update) : 'Never'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-gray-400">Threshold information not available</p>
            )}
          </div>
        </div>

        {/* Context Reasoning */}
        {contextStatus?.context_status?.adjustments && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Bell className="w-5 h-5 mr-2 text-yellow-400" />
              Current Context & Adjustments
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-3 text-green-400">Active Adjustments:</h3>
                <ul className="space-y-2">
                  {contextStatus.context_status.adjustments.map((adjustment, index) => (
                    <li key={index} className="text-sm bg-gray-700 rounded px-3 py-2">
                      {adjustment}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold mb-3 text-blue-400">Status:</h3>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    {contextStatus.context_status.is_prayer_time ? (
                      <Moon className="w-4 h-4 text-blue-400" />
                    ) : (
                      <Sun className="w-4 h-4 text-yellow-400" />
                    )}
                    <span className="text-sm">
                      {contextStatus.context_status.is_prayer_time ? 
                        `Prayer Time: ${contextStatus.context_status.prayer_info}` : 
                        'No active prayer time'
                      }
                    </span>
                  </div>
                  
                  <div className="text-sm">
                    <span className="text-gray-400">Final Multiplier: </span>
                    <span className="font-semibold text-green-400">
                      {contextStatus.context_status.final_multiplier}x
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Camera Distribution by Country */}
        {camerasbyCountry.country_cameras_map && Object.keys(camerasbyCountry.country_cameras_map).length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Camera className="w-5 h-5 mr-2 text-purple-400" />
              Camera Distribution by Country
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(camerasbyCountry.country_cameras_map).map(([country, cameras]) => (
                <div key={country} className="bg-gray-700 rounded-lg p-4">
                  <h3 className="font-semibold text-lg mb-2 capitalize text-blue-400">
                    {country.charAt(0).toUpperCase() + country.slice(1)}
                  </h3>
                  <div className="text-sm text-gray-300 mb-2">
                    {cameras.length} camera{cameras.length !== 1 ? 's' : ''}
                  </div>
                  <div className="text-xs text-gray-400">
                    Camera IDs: {cameras.slice(0, 3).join(', ')}
                    {cameras.length > 3 && ` +${cameras.length - 3} more`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={simulatePrayerTime}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-3 rounded-lg flex items-center justify-center space-x-2"
          >
            <Moon className="w-4 h-4" />
            <span>Simulate Prayer Time</span>
          </button>
          
          <button
            onClick={() => removeEvents('prayer_time')}
            disabled={loading}
            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 px-4 py-3 rounded-lg flex items-center justify-center space-x-2"
          >
            <Bell className="w-4 h-4" />
            <span>Clear Prayer Events</span>
          </button>
          
          <button
            onClick={loadThresholdInfo}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-3 rounded-lg flex items-center justify-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Refresh Status</span>
          </button>
        </div>

        {/* Add Custom Event */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-purple-400" />
            Add Custom Event
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2">Event Type</label>
              <select
                value={newEvent.event_type}
                onChange={(e) => setNewEvent({...newEvent, event_type: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="religious_festival">Religious Festival</option>
                <option value="cultural_festival">Cultural Festival</option>
                <option value="academic_break">Academic Break</option>
                <option value="political_tension">Political Tension</option>
                <option value="graduation">Graduation</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Crowd Multiplier</label>
              <input
                type="number"
                step="0.1"
                value={newEvent.crowd_multiplier}
                onChange={(e) => setNewEvent({...newEvent, crowd_multiplier: parseFloat(e.target.value)})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Start Time</label>
              <input
                type="datetime-local"
                value={newEvent.start_time}
                onChange={(e) => setNewEvent({...newEvent, start_time: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">End Time</label>
              <input
                type="datetime-local"
                value={newEvent.end_time}
                onChange={(e) => setNewEvent({...newEvent, end_time: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Target Countries</label>
            <div className="bg-gray-700 border border-gray-600 rounded px-3 py-2">
              {camerasbyCountry.country_cameras_map && Object.keys(camerasbyCountry.country_cameras_map).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(camerasbyCountry.country_cameras_map).map(([country, cameras]) => (
                    <label key={country} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={newEvent.target_countries.includes(country)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewEvent({
                              ...newEvent, 
                              target_countries: [...newEvent.target_countries, country]
                            });
                          } else {
                            setNewEvent({
                              ...newEvent, 
                              target_countries: newEvent.target_countries.filter(c => c !== country)
                            });
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">
                        {country.charAt(0).toUpperCase() + country.slice(1)} ({cameras.length} cameras)
                      </span>
                    </label>
                  ))}
                  <div className="text-xs text-gray-400 mt-2">
                    Leave unchecked to apply to all countries
                  </div>
                </div>
              ) : (
                <div className="text-gray-400 text-sm">No countries available</div>
              )}
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Description</label>
            <input
              type="text"
              placeholder="e.g., Eid Al-Fitr Celebration, Graduation Ceremony"
              value={newEvent.description}
              onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
            />
          </div>
          
          <button
            onClick={addEvent}
            disabled={loading}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-6 py-2 rounded-lg"
          >
            {loading ? 'Adding...' : 'Add Event'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DynamicThresholds;
