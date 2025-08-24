"""
Dynamic Context Agent for Location and Event-Based Threshold Management
Handles cultural, religious, and event-based crowd threshold adjustments
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class LocationContext:
    """Location-based context information"""
    country: str
    city: str
    timezone: str
    population_density: float  # people per km²
    cultural_context: str  # collectivist, individualist, mixed
    religious_majority: List[str]  # islam, christianity, hinduism, buddhism, etc.
    latitude: float
    longitude: float

@dataclass
class EventContext:
    """Event-based context information"""
    event_type: str  # prayer, festival, political, emergency, academic
    start_time: datetime
    end_time: datetime
    crowd_multiplier: float  # threshold adjustment factor
    description: str
    target_countries: List[str]  # specific countries this event affects
    affected_cameras: List[str] = None  # specific camera IDs affected
    is_active: bool = False

class DynamicContextAgent:
    """
    Intelligent agent that adjusts crowd thresholds based on:
    - Geographic location and population density
    - Religious prayer times (all religions)
    - Cultural events and festivals
    - Political or emergency situations
    - Academic calendar events
    """
    
    def __init__(self):
        self.base_thresholds = {
            'crowd_density': 5,
            'gathering_size': 8,
            'max_normal_density': 10
        }
        
        # Prayer time schedules (approximate times - would integrate with prayer API in production)
        self.prayer_schedules = {
            'islam': [
                ('fajr', 5, 30, 6, 0),      # Dawn prayer
                ('dhuhr', 12, 0, 13, 30),   # Noon prayer  
                ('asr', 15, 30, 16, 30),    # Afternoon prayer
                ('maghrib', 18, 0, 19, 0),  # Sunset prayer
                ('isha', 20, 0, 21, 0)      # Night prayer
            ],
            'christianity': [
                ('morning_service', 9, 0, 11, 0),    # Sunday morning service
                ('evening_service', 18, 0, 20, 0),   # Evening service
            ],
            'hinduism': [
                ('morning_puja', 6, 0, 8, 0),        # Morning worship
                ('evening_aarti', 18, 30, 20, 0),    # Evening worship
            ],
            'buddhism': [
                ('morning_meditation', 6, 0, 7, 30),  # Morning meditation
                ('evening_chanting', 18, 0, 19, 30),  # Evening chanting
            ]
        }
        
        # Population density thresholds by country category
        self.population_categories = {
            'very_high': 1000,  # >1000 people/km² (Singapore, Bangladesh, South Korea)
            'high': 300,        # 300-1000 people/km² (Japan, Germany, UK)
            'medium': 100,      # 100-300 people/km² (USA, China, France)
            'low': 50,          # 50-100 people/km² (Brazil, Turkey)
            'very_low': 50      # <50 people/km² (Canada, Australia, Russia)
        }
        
        # Cultural crowd tolerance factors
        self.cultural_factors = {
            'collectivist': 1.5,    # Higher tolerance for crowds
            'individualist': 0.8,   # Lower tolerance for crowds
            'mixed': 1.0           # Neutral tolerance
        }
        
        # Event-based multipliers
        self.event_multipliers = {
            'prayer_time': 2.0,      # Double threshold during prayer times
            'religious_festival': 3.0, # Triple threshold during festivals
            'academic_break': 0.7,    # Lower threshold during breaks
            'political_tension': 0.5,  # Much lower threshold during unrest
            'emergency': 0.3,         # Very low threshold during emergencies
            'graduation': 2.5,        # Higher threshold during graduation
            'cultural_festival': 2.2, # Higher threshold during cultural events
        }
        
        self.current_events: List[EventContext] = []
        self.location_context: Optional[LocationContext] = None
        self.camera_country_map: Dict[str, str] = {}  # camera_id -> country mapping
        self.country_cameras_map: Dict[str, List[str]] = {}  # country -> camera_ids mapping
        
    async def initialize_location_context(self, university_config: Dict) -> None:
        """Initialize location context from university configuration"""
        try:
            # Extract location info from university config
            country = university_config.get('country', 'Unknown')
            city = university_config.get('city', 'Unknown')
            center = university_config.get('center', {})
            
            # Estimate population density (in production, would use real data APIs)
            population_density = self._estimate_population_density(country, city)
            
            # Determine cultural context
            cultural_context = self._determine_cultural_context(country)
            
            # Determine religious majority
            religious_majority = self._determine_religious_majority(country)
            
            self.location_context = LocationContext(
                country=country,
                city=city,
                timezone='UTC',  # Would determine from coordinates in production
                population_density=population_density,
                cultural_context=cultural_context,
                religious_majority=religious_majority,
                latitude=center.get('lat', 0.0),
                longitude=center.get('lng', 0.0)
            )
            
            logger.info(f"Location context initialized for {city}, {country}")
            logger.info(f"Population density: {population_density}, Cultural: {cultural_context}")
            logger.info(f"Religious majority: {religious_majority}")
            
        except Exception as e:
            logger.error(f"Error initializing location context: {e}")
    
    async def register_cameras_by_country(self, university_config: Dict) -> None:
        """Register cameras with their country information"""
        try:
            country = university_config.get('country', 'Unknown')
            cameras = university_config.get('cameras', [])
            
            # Map each camera to its country
            for camera in cameras:
                camera_id = camera.get('camera_id')
                if camera_id:
                    self.camera_country_map[camera_id] = country
                    
                    # Add to country -> cameras mapping
                    if country not in self.country_cameras_map:
                        self.country_cameras_map[country] = []
                    if camera_id not in self.country_cameras_map[country]:
                        self.country_cameras_map[country].append(camera_id)
            
            logger.info(f"Registered {len(cameras)} cameras for country: {country}")
            logger.info(f"Camera-country mapping: {self.camera_country_map}")
            
        except Exception as e:
            logger.error(f"Error registering cameras by country: {e}")
    
    def _estimate_population_density(self, country: str, city: str) -> float:
        """Estimate population density based on country/city"""
        # Simplified mapping - in production would use real demographic APIs
        density_map = {
            'lebanon': 667,     # Lebanon population density
            'usa': 36,          # USA population density  
            'uk': 275,          # UK population density
            'japan': 347,       # Japan population density
            'singapore': 8358,  # Singapore population density
            'bangladesh': 1265, # Bangladesh population density
            'canada': 4,        # Canada population density
            'australia': 3,     # Australia population density
        }
        
        # City modifiers (cities are typically 3-5x more dense than country average)
        city_multiplier = 4.0 if city.lower() != 'unknown' else 1.0
        
        base_density = density_map.get(country.lower(), 100)  # Default to medium
        return base_density * city_multiplier
    
    def _determine_cultural_context(self, country: str) -> str:
        """Determine cultural context based on country"""
        collectivist_countries = ['japan', 'south korea', 'china', 'singapore', 'lebanon', 'uae']
        individualist_countries = ['usa', 'uk', 'canada', 'australia', 'germany', 'france']
        
        country_lower = country.lower()
        if country_lower in collectivist_countries:
            return 'collectivist'
        elif country_lower in individualist_countries:
            return 'individualist'
        else:
            return 'mixed'
    
    def _determine_religious_majority(self, country: str) -> List[str]:
        """Determine religious majority based on country"""
        religious_map = {
            'lebanon': ['islam', 'christianity'],
            'usa': ['christianity'],
            'uk': ['christianity'],
            'japan': ['buddhism'],
            'singapore': ['buddhism', 'islam', 'hinduism'],
            'bangladesh': ['islam'],
            'india': ['hinduism', 'islam'],
            'china': ['buddhism'],
            'uae': ['islam'],
            'saudi arabia': ['islam'],
        }
        
        return religious_map.get(country.lower(), ['christianity'])  # Default
    
    async def add_event(self, event: EventContext) -> None:
        """Add a new event that affects crowd thresholds"""
        self.current_events.append(event)
        logger.info(f"Added event: {event.event_type} - {event.description}")
    
    async def remove_event(self, event_type: str) -> None:
        """Remove events of specific type"""
        self.current_events = [e for e in self.current_events if e.event_type != event_type]
        logger.info(f"Removed events of type: {event_type}")
    
    async def add_custom_event(self, event_type: str, description: str, 
                             duration_hours: int, crowd_multiplier: float,
                             target_countries: List[str] = None) -> Dict:
        """Add a custom event that affects thresholds for specific countries"""
        try:
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(hours=duration_hours)
            
            # If no target countries specified, use current location
            if not target_countries:
                target_countries = [self.location_context.country] if self.location_context else ['Unknown']
            
            # Find affected cameras for target countries
            affected_cameras = []
            for country in target_countries:
                if country in self.country_cameras_map:
                    affected_cameras.extend(self.country_cameras_map[country])
            
            event = EventContext(
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                crowd_multiplier=crowd_multiplier,
                description=description,
                target_countries=target_countries,
                affected_cameras=affected_cameras,
                is_active=True
            )
            
            self.current_events.append(event)
            
            logger.info(f"Added custom event '{description}' affecting {len(affected_cameras)} cameras in countries: {target_countries}")
            
            return {
                "message": f"Event '{description}' added successfully",
                "affected_countries": target_countries,
                "affected_cameras": affected_cameras,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "crowd_multiplier": crowd_multiplier
            }
            
        except Exception as e:
            logger.error(f"Error adding custom event: {e}")
            return {"error": str(e)}
    
    def _is_prayer_time(self, current_time: datetime) -> Tuple[bool, str, float]:
        """Check if current time is within prayer time for any religion"""
        if not self.location_context:
            return False, "", 1.0
        
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_total_minutes = current_hour * 60 + current_minute
        
        for religion in self.location_context.religious_majority:
            if religion in self.prayer_schedules:
                for prayer_name, start_h, start_m, end_h, end_m in self.prayer_schedules[religion]:
                    start_minutes = start_h * 60 + start_m
                    end_minutes = end_h * 60 + end_m
                    
                    if start_minutes <= current_total_minutes <= end_minutes:
                        multiplier = self.event_multipliers['prayer_time']
                        return True, f"{religion}_{prayer_name}", multiplier
        
        return False, "", 1.0
    
    def _get_population_density_multiplier(self) -> float:
        """Get crowd threshold multiplier based on population density"""
        if not self.location_context:
            return 1.0
        
        density = self.location_context.population_density
        
        if density > self.population_categories['very_high']:
            return 2.0  # Much higher tolerance in very dense areas
        elif density > self.population_categories['high']:
            return 1.5  # Higher tolerance in dense areas
        elif density > self.population_categories['medium']:
            return 1.0  # Normal tolerance
        elif density > self.population_categories['low']:
            return 0.8  # Lower tolerance in sparse areas
        else:
            return 0.6  # Much lower tolerance in very sparse areas
    
    def _get_cultural_multiplier(self) -> float:
        """Get crowd threshold multiplier based on cultural context"""
        if not self.location_context:
            return 1.0
        
        return self.cultural_factors.get(self.location_context.cultural_context, 1.0)
    
    def _get_active_event_multiplier(self, current_time: datetime) -> Tuple[float, List[str]]:
        """Get multiplier for currently active events"""
        active_multipliers = []
        active_events = []
        
        for event in self.current_events:
            if event.start_time <= current_time <= event.end_time:
                active_multipliers.append(event.crowd_multiplier)
                active_events.append(f"{event.event_type}: {event.description}")
        
        # Take the maximum multiplier if multiple events are active
        final_multiplier = max(active_multipliers) if active_multipliers else 1.0
        
        return final_multiplier, active_events
    
    async def get_dynamic_thresholds(self, current_time: Optional[datetime] = None) -> Dict:
        """
        Calculate dynamic crowd thresholds based on current context
        Returns adjusted thresholds with reasoning
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Start with base thresholds
        adjusted_thresholds = self.base_thresholds.copy()
        adjustments = []
        
        # 1. Check prayer time
        is_prayer, prayer_info, prayer_multiplier = self._is_prayer_time(current_time)
        if is_prayer:
            adjustments.append(f"Prayer time ({prayer_info}): x{prayer_multiplier}")
        
        # 2. Population density adjustment
        density_multiplier = self._get_population_density_multiplier()
        adjustments.append(f"Population density: x{density_multiplier}")
        
        # 3. Cultural context adjustment
        cultural_multiplier = self._get_cultural_multiplier()
        adjustments.append(f"Cultural context: x{cultural_multiplier}")
        
        # 4. Active events adjustment
        event_multiplier, active_events = self._get_active_event_multiplier(current_time)
        if event_multiplier != 1.0:
            adjustments.append(f"Active events: x{event_multiplier}")
            adjustments.extend(active_events)
        
        # Calculate final multiplier (prayer time takes precedence)
        if is_prayer:
            final_multiplier = prayer_multiplier * density_multiplier * cultural_multiplier
        else:
            final_multiplier = density_multiplier * cultural_multiplier * event_multiplier
        
        # Apply adjustments
        for key in adjusted_thresholds:
            adjusted_thresholds[key] = int(self.base_thresholds[key] * final_multiplier)
        
        result = {
            'thresholds': adjusted_thresholds,
            'base_thresholds': self.base_thresholds,
            'final_multiplier': round(final_multiplier, 2),
            'adjustments': adjustments,
            'is_prayer_time': is_prayer,
            'prayer_info': prayer_info if is_prayer else None,
            'location_context': {
                'country': self.location_context.country if self.location_context else 'Unknown',
                'city': self.location_context.city if self.location_context else 'Unknown',
                'population_density': self.location_context.population_density if self.location_context else 0,
                'cultural_context': self.location_context.cultural_context if self.location_context else 'mixed'
            },
            'active_events': active_events[1] if len(active_events) > 1 else [],
            'timestamp': current_time.isoformat()
        }
        
        return result
    
    async def get_camera_specific_thresholds(self, camera_id: str, current_time: Optional[datetime] = None) -> Dict:
        """
        Calculate dynamic thresholds specific to a camera based on its country and active events
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Get camera's country
        camera_country = self.camera_country_map.get(camera_id, 'Unknown')
        
        # Start with base thresholds
        adjusted_thresholds = self.base_thresholds.copy()
        adjustments = []
        
        # 1. Check prayer time (applies to all cameras in religious areas)
        is_prayer, prayer_info, prayer_multiplier = self._is_prayer_time(current_time)
        if is_prayer:
            adjustments.append(f"Prayer time ({prayer_info}): x{prayer_multiplier}")
        
        # 2. Population density adjustment (based on camera's country)
        density_multiplier = self._get_population_density_multiplier()
        adjustments.append(f"Population density ({camera_country}): x{density_multiplier}")
        
        # 3. Cultural context adjustment
        cultural_multiplier = self._get_cultural_multiplier()
        adjustments.append(f"Cultural context: x{cultural_multiplier}")
        
        # 4. Camera-specific event adjustments
        camera_event_multiplier = 1.0
        camera_events = []
        
        for event in self.current_events:
            if not event.is_active:
                continue
                
            # Check if event is currently active
            if event.start_time <= current_time <= event.end_time:
                # Check if this camera is affected by the event
                if (camera_country in event.target_countries or 
                    (event.affected_cameras and camera_id in event.affected_cameras)):
                    camera_event_multiplier = max(camera_event_multiplier, event.crowd_multiplier)
                    camera_events.append(f"{event.event_type}: {event.description}")
        
        if camera_event_multiplier != 1.0:
            adjustments.append(f"Camera-specific events: x{camera_event_multiplier}")
            adjustments.extend(camera_events)
        
        # Calculate final multiplier
        if is_prayer:
            final_multiplier = prayer_multiplier * density_multiplier * cultural_multiplier
        else:
            final_multiplier = density_multiplier * cultural_multiplier * camera_event_multiplier
        
        # Apply adjustments
        for key in adjusted_thresholds:
            adjusted_thresholds[key] = int(self.base_thresholds[key] * final_multiplier)
        
        result = {
            'camera_id': camera_id,
            'camera_country': camera_country,
            'thresholds': adjusted_thresholds,
            'base_thresholds': self.base_thresholds,
            'final_multiplier': round(final_multiplier, 2),
            'adjustments': adjustments,
            'is_prayer_time': is_prayer,
            'prayer_info': prayer_info if is_prayer else None,
            'camera_specific_events': camera_events,
            'timestamp': current_time.isoformat()
        }
        
        return result
    
    async def schedule_recurring_events(self) -> None:
        """Schedule recurring events like prayer times"""
        if not self.location_context:
            return
        
        # Schedule prayer time events for the next 24 hours
        current_time = datetime.now()
        
        for religion in self.location_context.religious_majority:
            if religion in self.prayer_schedules:
                for prayer_name, start_h, start_m, end_h, end_m in self.prayer_schedules[religion]:
                    # Create event for today
                    start_time = current_time.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                    end_time = current_time.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
                    
                    if end_time > current_time:  # Only schedule future events
                        event = EventContext(
                            event_type='prayer_time',
                            start_time=start_time,
                            end_time=end_time,
                            crowd_multiplier=self.event_multipliers['prayer_time'],
                            description=f"{religion.title()} {prayer_name.title()} Prayer Time",
                            is_active=False
                        )
                        await self.add_event(event)

# Global instance for the dynamic context agent
dynamic_context_agent = DynamicContextAgent()
