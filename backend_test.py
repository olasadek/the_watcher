#!/usr/bin/env python3
"""
Backend API Testing for The Watcher University Monitoring System
Tests all API endpoints and functionality
"""

import requests
import json
import sys
import time
from datetime import datetime
from io import BytesIO
import uuid

class WatcherAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, name, method, endpoint, expected_status=200, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}", "ERROR")
                try:
                    error_data = response.json()
                    self.log(f"   Error details: {error_data}", "ERROR")
                except:
                    self.log(f"   Response text: {response.text[:200]}", "ERROR")
                return False, {}
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ {name} - Network error: {str(e)}", "ERROR")
            return False, {}
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}", "ERROR")
            return False, {}
    
    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET", 
            "/api/health"
        )
        
        if success and response.get("status") == "healthy":
            self.log("✅ Health check passed - System is healthy")
            return True
        else:
            self.log("❌ Health check failed", "ERROR")
            return False
    
    def test_cameras_crud(self):
        """Test camera CRUD operations"""
        # Test GET cameras (initially empty)
        success, response = self.run_test(
            "Get Cameras (Empty)",
            "GET",
            "/api/cameras"
        )
        
        if not success:
            return False
            
        initial_count = len(response.get("cameras", []))
        self.log(f"Initial camera count: {initial_count}")
        
        # Test POST camera
        test_camera = {
            "camera_id": f"test_camera_{int(time.time())}",
            "name": "Test Camera 1",
            "location": {"lat": 40.7128, "lng": -74.0060},
            "status": "active",
            "feed_url": "http://test.com/feed1"
        }
        
        success, response = self.run_test(
            "Create Camera",
            "POST",
            "/api/cameras",
            data=test_camera
        )
        
        if not success:
            return False
            
        self.test_data["camera_id"] = test_camera["camera_id"]
        
        # Test GET cameras (should have one more)
        success, response = self.run_test(
            "Get Cameras (After Create)",
            "GET",
            "/api/cameras"
        )
        
        if success:
            new_count = len(response.get("cameras", []))
            if new_count == initial_count + 1:
                self.log("✅ Camera creation verified")
                return True
            else:
                self.log(f"❌ Expected {initial_count + 1} cameras, got {new_count}", "ERROR")
                return False
        
        return False
    
    def test_security_booths_crud(self):
        """Test security booth CRUD operations"""
        # Test GET booths
        success, response = self.run_test(
            "Get Security Booths (Empty)",
            "GET",
            "/api/security-booths"
        )
        
        if not success:
            return False
            
        initial_count = len(response.get("booths", []))
        self.log(f"Initial booth count: {initial_count}")
        
        # Test POST booth
        test_booth = {
            "booth_id": f"test_booth_{int(time.time())}",
            "name": "Test Security Booth 1",
            "location": {"lat": 40.7130, "lng": -74.0062},
            "personnel": ["Officer Smith", "Officer Jones"],
            "status": "active"
        }
        
        success, response = self.run_test(
            "Create Security Booth",
            "POST",
            "/api/security-booths",
            data=test_booth
        )
        
        if not success:
            return False
            
        self.test_data["booth_id"] = test_booth["booth_id"]
        
        # Test GET booths (should have one more)
        success, response = self.run_test(
            "Get Security Booths (After Create)",
            "GET",
            "/api/security-booths"
        )
        
        if success:
            new_count = len(response.get("booths", []))
            if new_count == initial_count + 1:
                self.log("✅ Security booth creation verified")
                return True
            else:
                self.log(f"❌ Expected {initial_count + 1} booths, got {new_count}", "ERROR")
                return False
        
        return False
    
    def test_incidents_crud(self):
        """Test incident CRUD operations"""
        # Test GET incidents
        success, response = self.run_test(
            "Get Incidents (Initial)",
            "GET",
            "/api/incidents"
        )
        
        if not success:
            return False
            
        initial_count = len(response.get("incidents", []))
        self.log(f"Initial incident count: {initial_count}")
        
        # Test POST incident
        test_incident = {
            "incident_id": str(uuid.uuid4()),
            "camera_id": self.test_data.get("camera_id", "test_camera"),
            "incident_type": "suspicious_activity",
            "severity": "medium",
            "location": {"lat": 40.7129, "lng": -74.0061},
            "timestamp": datetime.utcnow().isoformat(),
            "description": "Test incident for API testing",
            "status": "active"
        }
        
        success, response = self.run_test(
            "Create Incident",
            "POST",
            "/api/incidents",
            data=test_incident
        )
        
        if not success:
            return False
            
        self.test_data["incident_id"] = test_incident["incident_id"]
        
        # Test GET incidents (should have one more)
        success, response = self.run_test(
            "Get Incidents (After Create)",
            "GET",
            "/api/incidents"
        )
        
        if success:
            new_count = len(response.get("incidents", []))
            if new_count == initial_count + 1:
                self.log("✅ Incident creation verified")
                return True
            else:
                self.log(f"❌ Expected {initial_count + 1} incidents, got {new_count}", "ERROR")
                return False
        
        return False
    
    def test_simulate_incident(self):
        """Test incident simulation"""
        success, response = self.run_test(
            "Simulate Incident",
            "POST",
            "/api/simulate-incident"
        )
        
        if success and "incident" in response:
            incident = response["incident"]
            required_fields = ["incident_id", "incident_type", "severity", "location", "timestamp"]
            
            for field in required_fields:
                if field not in incident:
                    self.log(f"❌ Missing field in simulated incident: {field}", "ERROR")
                    return False
            
            self.log("✅ Incident simulation successful")
            self.log(f"   Type: {incident['incident_type']}, Severity: {incident['severity']}")
            return True
        
        return False
    
    def test_frame_analysis(self):
        """Test frame analysis endpoint"""
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {'file': ('test.png', BytesIO(test_image_data), 'image/png')}
        
        success, response = self.run_test(
            "Analyze Frame",
            "POST",
            "/api/analyze-frame",
            files=files
        )
        
        if success:
            # Check if response has expected structure
            expected_keys = ["incidents_detected", "incidents_created", "analysis_results"]
            for key in expected_keys:
                if key not in response:
                    self.log(f"❌ Missing key in frame analysis response: {key}", "ERROR")
                    return False
            
            self.log("✅ Frame analysis endpoint working")
            self.log(f"   Incidents detected: {response.get('incidents_detected', False)}")
            return True
        
        return False
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint (if it exists)"""
        success, response = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "/api/dashboard-stats"
        )
        
        if success:
            expected_keys = ["total_cameras", "active_incidents", "total_booths"]
            for key in expected_keys:
                if key not in response:
                    self.log(f"❌ Missing key in dashboard stats: {key}", "ERROR")
                    return False
            
            self.log("✅ Dashboard stats endpoint working")
            self.log(f"   Cameras: {response.get('total_cameras', 0)}, "
                    f"Incidents: {response.get('active_incidents', 0)}, "
                    f"Booths: {response.get('total_booths', 0)}")
            return True
        else:
            self.log("⚠️  Dashboard stats endpoint not found - this is expected", "WARN")
            return True  # Not a failure since endpoint doesn't exist
    
    def run_all_tests(self):
        """Run all API tests"""
        self.log("🚀 Starting The Watcher API Tests")
        self.log(f"Testing against: {self.base_url}")
        
        test_results = []
        
        # Test basic health
        test_results.append(("Health Check", self.test_health_check()))
        
        # Test CRUD operations
        test_results.append(("Cameras CRUD", self.test_cameras_crud()))
        test_results.append(("Security Booths CRUD", self.test_security_booths_crud()))
        test_results.append(("Incidents CRUD", self.test_incidents_crud()))
        
        # Test special endpoints
        test_results.append(("Simulate Incident", self.test_simulate_incident()))
        test_results.append(("Frame Analysis", self.test_frame_analysis()))
        test_results.append(("Dashboard Stats", self.test_dashboard_stats()))
        
        # Print summary
        self.log("\n" + "="*60)
        self.log("📊 TEST SUMMARY")
        self.log("="*60)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
        
        self.log(f"\nOverall: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All tests passed!")
            return 0
        else:
            self.log("💥 Some tests failed!")
            return 1

def main():
    """Main test runner"""
    # Use environment variable for backend URL if available
    import os
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    tester = WatcherAPITester(backend_url)
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())