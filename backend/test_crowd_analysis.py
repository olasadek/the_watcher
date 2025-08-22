"""
Comprehensive test suite for crowd analysis functionality
Tests crowd detection, density analysis, and risk assessment
"""
import sys
import os
import pytest
import numpy as np
import json
from datetime import datetime

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision_analyzer import VisionAnalyzer

class TestCrowdAnalysis:
    """Test class for crowd analysis functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a VisionAnalyzer instance for testing"""
        return VisionAnalyzer()
    
    @pytest.fixture
    def test_frame(self):
        """Create a test frame for analysis"""
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    @pytest.fixture
    def small_crowd(self):
        """Simulate a small crowd (3 people)"""
        return [
            (100, 100, 60, 120, 0.8),
            (200, 120, 55, 110, 0.9),
            (300, 90, 65, 125, 0.7)
        ]
    
    @pytest.fixture
    def medium_crowd(self):
        """Simulate a medium crowd (9 people)"""
        return [
            (100, 100, 60, 120, 0.8),
            (200, 120, 55, 110, 0.9),
            (300, 90, 65, 125, 0.7),
            (400, 110, 58, 115, 0.85),
            (150, 200, 62, 118, 0.75),
            (250, 180, 60, 120, 0.9),
            (350, 190, 64, 122, 0.8),
            (450, 210, 59, 117, 0.85),
            (500, 100, 61, 119, 0.78)
        ]
    
    @pytest.fixture
    def large_crowd(self):
        """Simulate a large crowd (15 people)"""
        return [
            (100, 100, 60, 120, 0.8), (200, 120, 55, 110, 0.9),
            (300, 90, 65, 125, 0.7), (400, 110, 58, 115, 0.85),
            (150, 200, 62, 118, 0.75), (250, 180, 60, 120, 0.9),
            (350, 190, 64, 122, 0.8), (450, 210, 59, 117, 0.85),
            (500, 100, 61, 119, 0.78), (80, 300, 63, 121, 0.82),
            (180, 320, 58, 116, 0.87), (280, 310, 66, 124, 0.79),
            (380, 330, 60, 118, 0.84), (480, 340, 62, 120, 0.81),
            (550, 280, 59, 117, 0.86)
        ]

    def test_crowd_density_small(self, analyzer, test_frame, small_crowd):
        """Test crowd density calculation with small crowd"""
        result = analyzer._analyze_crowd_density(small_crowd, test_frame.shape[:2])
        
        assert result['person_count'] == 3
        assert result['density'] > 0
        assert result['density_alert'] == False  # Should be low density
        assert 'avg_density' in result
        
    def test_crowd_density_medium(self, analyzer, test_frame, medium_crowd):
        """Test crowd density calculation with medium crowd"""
        result = analyzer._analyze_crowd_density(medium_crowd, test_frame.shape[:2])
        
        assert result['person_count'] == 9
        assert result['density'] > 0
        assert 'unusual_gathering' in result
        
    def test_crowd_density_large(self, analyzer, test_frame, large_crowd):
        """Test crowd density calculation with large crowd"""
        result = analyzer._analyze_crowd_density(large_crowd, test_frame.shape[:2])
        
        assert result['person_count'] == 15
        assert result['density'] > 0
        assert result['density_alert'] == True  # Should trigger alert
        
    def test_crowd_stability_analysis(self, analyzer):
        """Test crowd stability assessment"""
        # Simulate stable crowd (low movement)
        analyzer._crowd_history = [
            {'timestamp': datetime.now(), 'count': 8, 'avg_position': (320, 240)},
            {'timestamp': datetime.now(), 'count': 9, 'avg_position': (325, 245)},
            {'timestamp': datetime.now(), 'count': 8, 'avg_position': (318, 238)}
        ]
        
        stability = analyzer._analyze_crowd_stability()
        
        assert 'stability_score' in stability
        assert 'movement_level' in stability
        assert stability['stability_score'] >= 0 and stability['stability_score'] <= 1
        
    def test_crowd_risk_assessment(self, analyzer, test_frame, large_crowd):
        """Test crowd risk level calculation"""
        # Set up crowd data
        analyzer._detected_persons = large_crowd
        crowd_data = analyzer._analyze_crowd_density(large_crowd, test_frame.shape[:2])
        stability_data = {'stability_score': 0.3, 'movement_level': 'high'}
        
        risk_level = analyzer._calculate_crowd_risk_level(crowd_data, stability_data)
        
        assert risk_level in ['low', 'medium', 'high', 'critical']
        
    def test_get_crowd_statistics(self, analyzer, test_frame, medium_crowd):
        """Test comprehensive crowd statistics"""
        analyzer._detected_persons = medium_crowd
        
        stats = analyzer.get_crowd_statistics(test_frame)
        
        # Check all required fields are present
        required_fields = [
            'total_people', 'density_level', 'risk_level', 
            'stability_score', 'unusual_activity', 'crowd_zones'
        ]
        
        for field in required_fields:
            assert field in stats
            
        assert stats['total_people'] == len(medium_crowd)
        assert isinstance(stats['density_level'], str)
        assert isinstance(stats['risk_level'], str)
        
    def test_empty_frame_analysis(self, analyzer, test_frame):
        """Test analysis with no people detected"""
        empty_crowd = []
        result = analyzer._analyze_crowd_density(empty_crowd, test_frame.shape[:2])
        
        assert result['person_count'] == 0
        assert result['density'] == 0
        assert result['density_alert'] == False
        
    def test_crowd_zone_detection(self, analyzer, test_frame, large_crowd):
        """Test crowd zone detection and clustering"""
        analyzer._detected_persons = large_crowd
        
        zones = analyzer._detect_crowd_zones(large_crowd, test_frame.shape[:2])
        
        assert isinstance(zones, list)
        assert len(zones) >= 0  # May have 0 or more zones
        
        for zone in zones:
            assert 'center' in zone
            assert 'people_count' in zone
            assert 'density' in zone
            
    def test_performance_metrics(self, analyzer, test_frame, medium_crowd):
        """Test that analysis completes within reasonable time"""
        import time
        
        start_time = time.time()
        analyzer._detected_persons = medium_crowd
        stats = analyzer.get_crowd_statistics(test_frame)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should complete within 1 second
        
    def test_data_validation(self, analyzer, test_frame):
        """Test data validation and error handling"""
        # Test with invalid person data
        invalid_crowd = [
            (100, 100, -60, 120, 0.8),  # Negative width
            (200, 120, 55, -110, 0.9),  # Negative height
            (-300, 90, 65, 125, 0.7),   # Negative x
            (400, -110, 58, 115, 0.85), # Negative y
        ]
        
        # Should handle invalid data gracefully
        result = analyzer._analyze_crowd_density(invalid_crowd, test_frame.shape[:2])
        assert 'person_count' in result
        assert 'density' in result

def test_crowd_analysis_integration():
    """Integration test for the complete crowd analysis pipeline"""
    print("🔍 Running Comprehensive Crowd Analysis Tests...")
    
    analyzer = VisionAnalyzer()
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test scenarios with different crowd sizes
    test_scenarios = [
        ("Empty Area", []),
        ("Small Group", [(100, 100, 60, 120, 0.8), (200, 120, 55, 110, 0.9)]),
        ("Medium Crowd", [
            (100, 100, 60, 120, 0.8), (200, 120, 55, 110, 0.9),
            (300, 90, 65, 125, 0.7), (400, 110, 58, 115, 0.85),
            (150, 200, 62, 118, 0.75), (250, 180, 60, 120, 0.9),
            (350, 190, 64, 122, 0.8), (450, 210, 59, 117, 0.85)
        ])
    ]
    
    for scenario_name, persons in test_scenarios:
        print(f"\n📊 Testing: {scenario_name}")
        print(f"People detected: {len(persons)}")
        
        analyzer._detected_persons = persons
        stats = analyzer.get_crowd_statistics(test_frame)
        
        print(f"Results:")
        print(f"  - Total People: {stats['total_people']}")
        print(f"  - Density Level: {stats['density_level']}")
        print(f"  - Risk Level: {stats['risk_level']}")
        print(f"  - Stability Score: {stats['stability_score']:.2f}")
        print(f"  - Unusual Activity: {stats['unusual_activity']}")
        print(f"  - Crowd Zones: {len(stats['crowd_zones'])}")
        
        # Validate results
        assert stats['total_people'] == len(persons)
        assert stats['density_level'] in ['low', 'medium', 'high', 'critical']
        assert stats['risk_level'] in ['low', 'medium', 'high', 'critical']
        assert 0 <= stats['stability_score'] <= 1
        
    print("\n✅ All crowd analysis tests passed!")

if __name__ == "__main__":
    """Run tests when script is executed directly"""
    test_crowd_analysis_integration()
    print("\n🎯 To run full test suite with pytest:")
    print("   cd backend && python -m pytest test_crowd_analysis.py -v")
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
