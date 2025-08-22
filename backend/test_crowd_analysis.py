"""
Test script for crowd analysis functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision_analyzer import VisionAnalyzer
import cv2
import numpy as np
import json

def test_crowd_analysis():
    """Test the crowd analysis functionality"""
    
    # Initialize analyzer
    analyzer = VisionAnalyzer()
    
    # Create a test frame with multiple people (simulated)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Simulate detected persons (normally from HOG detector)
    # Format: [(x, y, w, h, confidence), ...]
    simulated_persons = [
        (100, 100, 60, 120, 0.8),  # Person 1
        (200, 120, 55, 110, 0.9),  # Person 2
        (300, 90, 65, 125, 0.7),   # Person 3
        (400, 110, 58, 115, 0.85), # Person 4
        (150, 200, 62, 118, 0.75), # Person 5
        (250, 180, 60, 120, 0.9),  # Person 6
        (350, 190, 64, 122, 0.8),  # Person 7
        (450, 210, 59, 117, 0.85), # Person 8
        (500, 100, 61, 119, 0.78), # Person 9
    ]
    
    print("🔍 Testing Crowd Analysis...")
    print(f"Simulating {len(simulated_persons)} detected persons")
    
    # Manually set the persons for testing
    analyzer._detected_persons = simulated_persons
    
    # Test crowd density analysis
    crowd_analysis = analyzer._analyze_crowd_density(simulated_persons, test_frame.shape[:2])
    
    print("\n📊 Crowd Analysis Results:")
    print(f"Person Count: {crowd_analysis['person_count']}")
    print(f"Density: {crowd_analysis['density']}")
    print(f"Average Density: {crowd_analysis['avg_density']}")
    print(f"Density Alert: {crowd_analysis['density_alert']}")
    print(f"Unusual Gathering: {crowd_analysis['unusual_gathering']}")
    print(f"Gathering Duration: {crowd_analysis['gathering_duration']} seconds")
    print(f"Crowd Stability: {crowd_analysis['crowd_stability']}")
    print(f"Risk Level: {crowd_analysis['risk_level']}")
    
    # Test with actual frame analysis
    print("\n🎯 Running Full Frame Analysis...")
    results = analyzer.analyze_frame(test_frame)
    
    print(f"Frame ID: {results['frame_id']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Incidents Detected: {len(results['incidents_detected'])}")
    
    for incident in results['incidents_detected']:
        print(f"  - {incident['type']}: {incident['confidence']:.2f} ({incident['severity']})")
    
    # Test crowd statistics
    print("\n📈 Crowd Statistics:")
    stats = analyzer.get_crowd_statistics()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Crowd analysis test completed!")
    
    return results

def test_threshold_configuration():
    """Test threshold configuration"""
    print("\n⚙️ Testing Threshold Configuration...")
    
    analyzer = VisionAnalyzer()
    
    # Test with different thresholds
    original_max_density = analyzer.max_normal_density
    original_gathering_size = analyzer.gathering_size_threshold
    
    print(f"Original max density: {original_max_density}")
    print(f"Original gathering size: {original_gathering_size}")
    
    # Update thresholds
    analyzer.max_normal_density = 5.0
    analyzer.gathering_size_threshold = 5
    
    print(f"Updated max density: {analyzer.max_normal_density}")
    print(f"Updated gathering size: {analyzer.gathering_size_threshold}")
    
    # Test with smaller gathering
    small_crowd = [(100, 100, 60, 120, 0.8) for i in range(6)]  # 6 people
    
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    crowd_analysis = analyzer._analyze_crowd_density(small_crowd, test_frame.shape[:2])
    
    print(f"Small crowd analysis - Unusual gathering: {crowd_analysis['unusual_gathering']}")
    print(f"Small crowd analysis - Risk level: {crowd_analysis['risk_level']}")
    
    print("✅ Threshold configuration test completed!")

if __name__ == "__main__":
    test_crowd_analysis()
    test_threshold_configuration()
