import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Settings, 
  Save, 
  MapPin, 
  Plus, 
  Trash2, 
  Camera, 
  Shield, 
  Globe,
  School,
  Edit3,
  Check,
  X
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Predefined university templates
const UNIVERSITY_TEMPLATES = {
  aub: {
    name: "American University of Beirut",
    country: "Lebanon",
    city: "Beirut",
    center: { lat: 33.9002, lng: 35.4818 },
    cameras: [
      { name: "Jafet Library Main Entrance", lat: 33.9008, lng: 35.4822 },
      { name: "Student Center Plaza", lat: 33.9000, lng: 35.4815 },
      { name: "Parking Lot A", lat: 33.8995, lng: 35.4810 },
      { name: "Dining Hall", lat: 33.9012, lng: 35.4828 },
      { name: "Gym Main Entrance", lat: 33.8990, lng: 35.4805 },
      { name: "Science Building", lat: 33.9015, lng: 35.4830 },
      { name: "North Dormitory", lat: 33.9020, lng: 35.4825 },
      { name: "Administration Building", lat: 33.9005, lng: 35.4818 }
    ],
    booths: [
      { name: "Main Gate Security", lat: 33.8998, lng: 35.4818, personnel: ["Officer Khalil", "Officer Maroun"] },
      { name: "North Campus Security", lat: 33.9015, lng: 35.4825, personnel: ["Officer Fares"] },
      { name: "South Campus Security", lat: 33.8985, lng: 35.4810, personnel: ["Officer Nadia", "Officer Ahmad"] },
      { name: "Central Plaza Security", lat: 33.9005, lng: 35.4820, personnel: ["Officer Layla", "Officer Omar"] }
    ]
  },
  mit: {
    name: "Massachusetts Institute of Technology",
    country: "USA",
    city: "Cambridge, MA",
    center: { lat: 42.3601, lng: -71.0942 },
    cameras: [
      { name: "Stata Center Entrance", lat: 42.3616, lng: -71.0909 },
      { name: "Student Center", lat: 42.3586, lng: -71.0954 },
      { name: "Library Main Entrance", lat: 42.3596, lng: -71.0935 },
      { name: "Parking Garage A", lat: 42.3575, lng: -71.0965 },
      { name: "Athletics Center", lat: 42.3565, lng: -71.0975 },
      { name: "Dormitory Complex", lat: 42.3620, lng: -71.0920 }
    ],
    booths: [
      { name: "Main Gate Security", lat: 42.3590, lng: -71.0945, personnel: ["Officer Johnson", "Officer Smith"] },
      { name: "West Campus Security", lat: 42.3570, lng: -71.0970, personnel: ["Officer Davis"] },
      { name: "East Campus Security", lat: 42.3610, lng: -71.0915, personnel: ["Officer Wilson", "Officer Brown"] }
    ]
  },
  oxford: {
    name: "University of Oxford",
    country: "UK",
    city: "Oxford",
    center: { lat: 51.7548, lng: -1.2544 },
    cameras: [
      { name: "Bodleian Library", lat: 51.7536, lng: -1.2544 },
      { name: "Radcliffe Camera", lat: 51.7539, lng: -1.2540 },
      { name: "Christ Church", lat: 51.7505, lng: -1.2559 },
      { name: "Ashmolean Museum", lat: 51.7558, lng: -1.2575 },
      { name: "Examination Schools", lat: 51.7520, lng: -1.2515 },
      { name: "University Parks", lat: 51.7610, lng: -1.2480 }
    ],
    booths: [
      { name: "Porter's Lodge - Main", lat: 51.7545, lng: -1.2550, personnel: ["Mr. Thompson", "Mr. Clarke"] },
      { name: "North Gate Security", lat: 51.7570, lng: -1.2520, personnel: ["Mr. Davies"] },
      { name: "South Gate Security", lat: 51.7515, lng: -1.2565, personnel: ["Ms. Williams", "Mr. Jones"] }
    ]
  },
  custom: {
    name: "Custom University",
    country: "Custom",
    city: "Custom City",
    center: { lat: 0, lng: 0 },
    cameras: [],
    booths: []
  }
};

function UniversityConfig() {
  const [selectedTemplate, setSelectedTemplate] = useState('aub');
  const [currentConfig, setCurrentConfig] = useState(UNIVERSITY_TEMPLATES.aub);
  const [isEditing, setIsEditing] = useState(false);
  const [editingCamera, setEditingCamera] = useState(null);
  const [editingBooth, setEditingBooth] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setCurrentConfig(UNIVERSITY_TEMPLATES[selectedTemplate]);
  }, [selectedTemplate]);

  const handleTemplateChange = (templateKey) => {
    setSelectedTemplate(templateKey);
    setIsEditing(false);
    setEditingCamera(null);
    setEditingBooth(null);
  };

  const addCamera = () => {
    const newCamera = {
      name: `New Camera ${currentConfig.cameras.length + 1}`,
      lat: currentConfig.center.lat + (Math.random() - 0.5) * 0.01,
      lng: currentConfig.center.lng + (Math.random() - 0.5) * 0.01
    };
    setCurrentConfig({
      ...currentConfig,
      cameras: [...currentConfig.cameras, newCamera]
    });
  };

  const addBooth = () => {
    const newBooth = {
      name: `New Security Booth ${currentConfig.booths.length + 1}`,
      lat: currentConfig.center.lat + (Math.random() - 0.5) * 0.01,
      lng: currentConfig.center.lng + (Math.random() - 0.5) * 0.01,
      personnel: ["Officer Name"]
    };
    setCurrentConfig({
      ...currentConfig,
      booths: [...currentConfig.booths, newBooth]
    });
  };

  const removeCamera = (index) => {
    setCurrentConfig({
      ...currentConfig,
      cameras: currentConfig.cameras.filter((_, i) => i !== index)
    });
  };

  const removeBooth = (index) => {
    setCurrentConfig({
      ...currentConfig,
      booths: currentConfig.booths.filter((_, i) => i !== index)
    });
  };

  const updateCamera = (index, field, value) => {
    const updatedCameras = [...currentConfig.cameras];
    updatedCameras[index] = { ...updatedCameras[index], [field]: value };
    setCurrentConfig({ ...currentConfig, cameras: updatedCameras });
  };

  const updateBooth = (index, field, value) => {
    const updatedBooths = [...currentConfig.booths];
    updatedBooths[index] = { ...updatedBooths[index], [field]: value };
    setCurrentConfig({ ...currentConfig, booths: updatedBooths });
  };

  const updateUniversityInfo = (field, value) => {
    setCurrentConfig({ ...currentConfig, [field]: value });
  };

  const saveConfiguration = async () => {
    try {
      setLoading(true);
      
      // Send configuration to backend
      const configData = {
        university: currentConfig.name,
        location: {
          country: currentConfig.country,
          city: currentConfig.city,
          center: currentConfig.center
        },
        cameras: currentConfig.cameras.map((cam, index) => ({
          camera_id: `cam_${index + 1}`,
          name: cam.name,
          location: { lat: cam.lat, lng: cam.lng },
          status: "active"
        })),
        booths: currentConfig.booths.map((booth, index) => ({
          booth_id: `booth_${index + 1}`,
          name: booth.name,
          location: { lat: booth.lat, lng: booth.lng },
          personnel: booth.personnel,
          status: "active"
        }))
      };

      await axios.post(`${BACKEND_URL}/api/configure-university`, configData);
      alert(`✅ ${currentConfig.name} configuration saved successfully!`);
      
    } catch (error) {
      console.error('Error saving configuration:', error);
      alert('❌ Failed to save configuration. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-bold flex items-center gap-3 mb-4">
            <School className="w-8 h-8 text-blue-400" />
            University Configuration
          </h1>
          <p className="text-gray-300">
            Choose a university template or create a custom configuration for your security system.
          </p>
        </div>

        {/* Template Selection */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5" />
            University Templates
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(UNIVERSITY_TEMPLATES).map(([key, template]) => (
              <button
                key={key}
                onClick={() => handleTemplateChange(key)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedTemplate === key
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <div className="text-left">
                  <div className="font-semibold">{template.name}</div>
                  <div className="text-sm text-gray-400">{template.city}, {template.country}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {template.cameras.length} cameras, {template.booths.length} booths
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* University Info */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Edit3 className="w-5 h-5" />
              University Information
            </h2>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={`px-3 py-1 rounded ${isEditing ? 'bg-red-600' : 'bg-blue-600'} hover:opacity-80`}
            >
              {isEditing ? <X className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">University Name</label>
              <input
                type="text"
                value={currentConfig.name}
                onChange={(e) => updateUniversityInfo('name', e.target.value)}
                disabled={!isEditing}
                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Country</label>
              <input
                type="text"
                value={currentConfig.country}
                onChange={(e) => updateUniversityInfo('country', e.target.value)}
                disabled={!isEditing}
                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Center Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={currentConfig.center.lat}
                onChange={(e) => updateUniversityInfo('center', { ...currentConfig.center, lat: parseFloat(e.target.value) })}
                disabled={!isEditing}
                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Center Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={currentConfig.center.lng}
                onChange={(e) => updateUniversityInfo('center', { ...currentConfig.center, lng: parseFloat(e.target.value) })}
                disabled={!isEditing}
                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        {/* Cameras Configuration */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Cameras ({currentConfig.cameras.length})
            </h2>
            <button
              onClick={addCamera}
              className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Camera
            </button>
          </div>
          
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {currentConfig.cameras.map((camera, index) => (
              <div key={index} className="flex items-center gap-2 p-2 bg-gray-700 rounded">
                <Camera className="w-4 h-4 text-blue-400" />
                <input
                  type="text"
                  value={camera.name}
                  onChange={(e) => updateCamera(index, 'name', e.target.value)}
                  className="flex-1 p-1 bg-gray-600 rounded text-sm"
                  placeholder="Camera name"
                />
                <input
                  type="number"
                  step="0.0001"
                  value={camera.lat}
                  onChange={(e) => updateCamera(index, 'lat', parseFloat(e.target.value))}
                  className="w-24 p-1 bg-gray-600 rounded text-sm"
                  placeholder="Lat"
                />
                <input
                  type="number"
                  step="0.0001"
                  value={camera.lng}
                  onChange={(e) => updateCamera(index, 'lng', parseFloat(e.target.value))}
                  className="w-24 p-1 bg-gray-600 rounded text-sm"
                  placeholder="Lng"
                />
                <button
                  onClick={() => removeCamera(index)}
                  className="text-red-400 hover:text-red-300 p-1"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Security Booths Configuration */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Security Booths ({currentConfig.booths.length})
            </h2>
            <button
              onClick={addBooth}
              className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Booth
            </button>
          </div>
          
          <div className="space-y-3 max-h-60 overflow-y-auto">
            {currentConfig.booths.map((booth, index) => (
              <div key={index} className="p-3 bg-gray-700 rounded">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-green-400" />
                  <input
                    type="text"
                    value={booth.name}
                    onChange={(e) => updateBooth(index, 'name', e.target.value)}
                    className="flex-1 p-1 bg-gray-600 rounded text-sm"
                    placeholder="Booth name"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={booth.lat}
                    onChange={(e) => updateBooth(index, 'lat', parseFloat(e.target.value))}
                    className="w-24 p-1 bg-gray-600 rounded text-sm"
                    placeholder="Lat"
                  />
                  <input
                    type="number"
                    step="0.0001"
                    value={booth.lng}
                    onChange={(e) => updateBooth(index, 'lng', parseFloat(e.target.value))}
                    className="w-24 p-1 bg-gray-600 rounded text-sm"
                    placeholder="Lng"
                  />
                  <button
                    onClick={() => removeBooth(index)}
                    className="text-red-400 hover:text-red-300 p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="ml-6">
                  <input
                    type="text"
                    value={booth.personnel.join(', ')}
                    onChange={(e) => updateBooth(index, 'personnel', e.target.value.split(', ').filter(p => p.trim()))}
                    className="w-full p-1 bg-gray-600 rounded text-sm"
                    placeholder="Personnel names (comma separated)"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <div className="text-center">
          <button
            onClick={saveConfiguration}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-8 py-3 rounded-lg flex items-center gap-3 mx-auto text-lg font-semibold"
          >
            <Save className="w-5 h-5" />
            {loading ? 'Saving Configuration...' : 'Save & Apply Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default UniversityConfig;
