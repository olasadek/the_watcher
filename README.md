# The Watcher - University Security System

## 🎯 Overview
"The Watcher" is a comprehensive AI-powered university monitoring system designed to detect and alert security personnel about various campus incidents in real-time. The system now features advanced crowd analysis, GPS-based mapping, and configurable university templates.

<img width="713" height="430" alt="the-watcher" src="https://github.com/user-attachments/assets/d5499c17-0b09-4f89-959f-28456051820d" />

## 🌟 Latest Updates (August 22, 2025)

### 🎓 University Configuration System
- **Multi-University Support**: Choose from predefined templates (AUB, MIT, Oxford) or create custom configurations
- **Dynamic Location Settings**: Configure university name, country, city, and GPS coordinates
- **Real-time Campus Customization**: Edit camera and security booth locations with live GPS coordinates

### 📊 Advanced Crowd Analysis
- **AI-Powered Crowd Monitoring**: Real-time crowd density analysis using OpenCV
- **Smart Crowd Metrics**: People counting, density calculation, and crowd stability assessment
- **Risk Assessment**: Automatic crowd risk level evaluation (Low/Medium/High/Critical)
- **Configurable Thresholds**: Customizable crowd density and stability parameters
- **Live Dashboard**: Dedicated crowd monitoring tab with real-time statistics

### 🗺️ GPS-Enabled Real Mapping
- **OpenStreetMap Integration**: Free alternative to Google Maps using Leaflet
- **Real GPS Coordinates**: Authentic university campus mapping with precise locations
- **Interactive Markers**: Custom icons for cameras, security booths, and incidents
- **Multi-Layer Visualization**: Toggle between cameras, booths, incidents, and routes
- **Location-Based Services**: GPS coordinate editing and real-time map updates

### 🎛️ Enhanced Dashboard System
- **Five-Tab Navigation**: Security Monitoring, Crowd Analysis, Campus Map, Real Map (GPS), University Config
- **Dynamic University Display**: Header shows current university name and location
- **Responsive UI**: Professional dark theme with improved user experience
- **Real-time Data Sync**: All components update automatically with configuration changes

## ✨ Core Features

### 🔍 Incident Detection
- **Person Fallen**: Detects students who have fallen using aspect ratio analysis
- **Fight Detection**: Identifies physical altercations between multiple people
- **Smoking Detection**: Monitors for smoking violations on campus
- **Suspicious Activity**: Flags unusual behavior patterns and loitering
- **Crowd Incidents**: Detects overcrowding and potential crowd-related risks

### 📈 Crowd Analysis Engine
- **People Counting**: Accurate real-time person detection and counting
- **Density Calculation**: Smart crowd density analysis per area
- **Movement Patterns**: Crowd flow and stability monitoring
- **Risk Assessment**: Automatic evaluation of crowd safety levels
- **Historical Tracking**: Crowd statistics storage and trend analysis

### 🗺️ Mapping & Location Services
- **Real GPS Integration**: Accurate campus mapping with OpenStreetMap
- **Interactive Visualization**: Custom markers and real-time location updates
- **Multi-University Support**: Configurable campus layouts for any university
- **Route Planning**: Smart routing to nearest security personnel
- **Geographic Data**: Store and manage GPS coordinates for all campus assets

### 🔊 Smart Alert System
- **Location-Based Routing**: Automatically notifies the closest security booth
- **Audio Notifications**: Sound alerts with different tones for priority levels
- **Real-time Updates**: WebSocket-based live notifications across all connected devices
- **Priority Classification**: High, medium, and low severity incident categorization
- **Crowd Alerts**: Special notifications for crowd-related incidents

### 📹 Camera Management
- **Live Webcam Integration**: Real-time analysis of computer camera feed
- **Multi-Camera Network**: Support for multiple camera locations across campus
- **GPS-Enabled Cameras**: Each camera has precise GPS coordinates
- **Dynamic Camera Addition**: Easy addition of new cameras with location mapping
- **University-Specific Configuration**: Camera setups tailored to each university

### 🛡️ Security Infrastructure
- **Security Booth Management**: Track booth locations with GPS coordinates
- **Distance Calculation**: Automatic routing using Haversine formula
- **Personnel Tracking**: Monitor officers with localized names and assignments
- **Response Management**: Track incident assignment and resolution status
- **Multi-University Personnel**: Support for different naming conventions and languages

## 🏗️ Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: MongoDB for storing cameras, incidents, security data, and university configurations
- **Real-time**: WebSocket connections for live updates
- **AI Integration**: OpenCV and MediaPipe for computer vision and crowd analysis
- **GPS Services**: Haversine distance calculation and coordinate management
- **API Endpoints**: 15+ RESTful endpoints including crowd analysis and university configuration

### Frontend (React)
- **Framework**: React 18 with functional components and hooks
- **Styling**: Tailwind CSS with professional dark security theme
- **Mapping**: Leaflet and react-leaflet for OpenStreetMap integration
- **Real-time**: WebSocket integration for live updates across all tabs
- **Camera Access**: react-webcam for computer camera integration
- **Icons**: Lucide React for comprehensive iconography
- **Multi-Page Navigation**: Five-tab system with dynamic content loading

### AI/ML Pipeline
- **Computer Vision**: OpenCV for motion detection and image analysis
- **Person Detection**: HOG descriptor with enhanced crowd counting
- **Crowd Analysis**: Advanced algorithms for density and stability calculation
- **Motion Analysis**: Background subtraction for movement detection
- **Behavioral Analysis**: Pattern recognition for suspicious activities
- **Fall Detection**: Aspect ratio analysis for fallen person detection
- **Risk Assessment**: Multi-factor crowd safety evaluation

## 🚀 Current System Status

### ✅ Fully Implemented Features
1. **Professional Security Dashboard** - Five-tab navigation with dynamic content
2. **Real-time Incident Detection** - AI-powered computer vision analysis
3. **Advanced Crowd Analysis** - Complete crowd monitoring and risk assessment
4. **GPS-Based Real Mapping** - OpenStreetMap integration with precise coordinates
5. **University Configuration System** - Multi-university support with templates
6. **Audio Alert System** - Sound notifications for different severity levels
7. **Dynamic Camera Management** - GPS-enabled camera network
8. **Location-Aware Security Booths** - Personnel management with GPS coordinates
9. **Incident Simulation** - Testing and demonstration capabilities
10. **Live Statistics** - Real-time dashboard metrics across all systems
11. **WebSocket Communication** - Real-time updates across all connected clients

### 🎓 Supported Universities
- **American University of Beirut (AUB)** - Beirut, Lebanon (Default)
- **Massachusetts Institute of Technology (MIT)** - Cambridge, USA
- **University of Oxford** - Oxford, UK
- **Custom University** - Fully configurable template

### 📊 System Statistics
- **Configurable Cameras**: Unlimited cameras with GPS coordinates
- **Security Booths**: Unlimited booths with personnel management
- **Crowd Monitoring**: Real-time analysis with configurable thresholds
- **GPS Mapping**: Precise coordinate management for any location
- **Response Time**: Sub-second incident detection and alerting

### 🔧 Technical Status
- **Backend API**: ✅ All 15+ endpoints tested and working
- **Database**: ✅ MongoDB with university configuration support
- **Frontend**: ✅ React application with five-tab navigation
- **Real-time Features**: ✅ WebSocket connections across all components
- **Computer Vision**: ✅ OpenCV with crowd analysis capabilities
- **Mapping System**: ✅ OpenStreetMap integration with GPS coordinates
- **Audio System**: ✅ Browser-based sound notifications
- **Configuration**: ✅ Dynamic university and campus setup

## 🎮 How to Use

### For Security Personnel:
1. **Monitor Dashboard**: View live camera feeds and comprehensive statistics
2. **Crowd Monitoring**: Track crowd density and receive crowd-related alerts
3. **Respond to Alerts**: Receive audio notifications for nearby incidents
4. **Map Navigation**: Use GPS-based real map for precise location tracking
5. **Manage Incidents**: Track and update incident status and assignments

### For University Administrators:
1. **Configure University**: Choose university template or create custom setup
2. **Setup Campus**: Configure camera and security booth locations with GPS
3. **Customize Settings**: Adjust crowd thresholds and monitoring parameters
4. **Monitor Performance**: Track system health across all monitoring systems
5. **Test System**: Use simulation features to verify all functionalities

### For System Administrators:
1. **University Setup**: Configure new universities with complete campus layouts
2. **GPS Configuration**: Set precise coordinates for all campus infrastructure
3. **Crowd Analysis**: Configure crowd monitoring parameters and thresholds
4. **Performance Monitoring**: Track system health and response times
5. **Multi-Campus Management**: Handle multiple university configurations

## 🔑 Key Differentiators

### Free AI Implementation
- No expensive API costs (OpenAI, etc.)
- Advanced OpenCV-based crowd analysis
- Fully self-contained detection pipeline
- Customizable detection algorithms

### Real GPS Integration
- OpenStreetMap integration (free alternative to Google Maps)
- Precise coordinate management for any global location
- Real-time GPS-based routing and distance calculation
- University-specific campus mapping

### Multi-University Support
- Predefined templates for major universities
- Completely configurable custom university setup
- Dynamic location and personnel management
- Cultural and linguistic adaptation support

### Advanced Crowd Intelligence
- Real-time crowd density analysis
- Crowd stability and movement pattern detection
- Risk assessment with configurable thresholds
- Historical crowd data and trend analysis

### Location-Aware Alerting
- Haversine formula for precise distance calculation
- Automatic routing to closest security booth
- GPS coordinate-based incident mapping
- Optimized response time through proximity routing

## 🌐 Access Information

### Application URLs
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs (FastAPI auto-generated)
- **Health Check**: http://localhost:8001/api/health

### How to Start
```bash
# Backend
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm install
npm start
```

### Service Status
- **Frontend**: ✅ React development server with five-tab navigation
- **Backend**: ✅ FastAPI server with all endpoints active
- **Database**: ✅ MongoDB with university configuration support
- **Mapping**: ✅ OpenStreetMap integration active
- **WebSocket**: ✅ Real-time communication across all components

## 🔮 Future Enhancement Opportunities

### Advanced AI Features
- Integration with more sophisticated ML models
- Facial recognition for person identification
- Weapon detection capabilities
- Behavioral pattern learning and prediction

### Extended Monitoring
- Mobile app for security personnel
- Email/SMS notification integration
- Integration with existing campus security systems
- Advanced analytics dashboard with historical reporting

### Scalability Improvements
- Multi-campus support expansion
- Cloud deployment capabilities
- Load balancing for high-traffic scenarios
- Advanced caching and performance optimization

### Global University Network
- Support for universities worldwide
- Multilingual interface support
- Cultural adaptation for different regions
- Integration with international security standards

---

**The Watcher** represents a complete, production-ready university monitoring solution that combines cutting-edge AI technology with practical security needs, providing a comprehensive platform for campus safety, crowd management, and incident response with global university support.
- **Icons**: Lucide React for professional security iconography

### AI/ML Pipeline
- **Computer Vision**: OpenCV for motion detection and image analysis
- **Person Detection**: HOG (Histogram of Oriented Gradients) descriptor
- **Motion Analysis**: Background subtraction for movement detection
- **Behavioral Analysis**: Pattern recognition for suspicious activities
- **Fall Detection**: Aspect ratio analysis for fallen person detection

## 🚀 Current System Status

### ✅ Fully Implemented Features
1. **Professional Security Dashboard** - Clean, dark-themed interface
2. **Real-time Incident Detection** - AI-powered computer vision analysis
3. **Audio Alert System** - Sound notifications for different severity levels
4. **Camera Management** - Add/manage cameras with location tracking
5. **Security Booth System** - Personnel and location management
6. **Incident Simulation** - Testing and demonstration capabilities
7. **Live Statistics** - Real-time dashboard metrics and analytics
8. **WebSocket Communication** - Real-time updates across all connected clients

### 📊 System Statistics
- **Active Cameras**: 4 configured cameras
- **Security Booths**: 4 security booths with personnel assigned
- **Recorded Incidents**: 8+ incidents in database
- **Response Time**: Sub-second incident detection and alerting

### 🔧 Technical Status
- **Backend API**: ✅ All 13 endpoints tested and working
- **Database**: ✅ MongoDB connected with proper data persistence
- **Frontend**: ✅ React application with full feature implementation
- **Real-time Features**: ✅ WebSocket connections and live updates
- **Computer Vision**: ✅ OpenCV integration with incident detection
- **Audio System**: ✅ Browser-based sound notifications

## 🎮 How to Use

### For Security Personnel:
1. **Monitor Dashboard**: View live camera feeds and incident statistics
2. **Respond to Alerts**: Receive audio notifications for nearby incidents
3. **Manage Incidents**: Track and update incident status and assignments
4. **Add Infrastructure**: Register new cameras and security booths

### For System Administrators:
1. **Test System**: Use "Simulate Incident" to verify alert functionality
2. **Analyze Feed**: Use "Analyze Frame" to test AI detection on webcam
3. **Monitor Performance**: Track system health and response times
4. **Manage Network**: Add/configure cameras and security booth locations

## 🔑 Key Differentiators

### Free AI Implementation
- No expensive API costs (OpenAI, etc.)
- Uses open-source computer vision libraries
- Fully self-contained detection pipeline
- Customizable detection algorithms

### Location-Aware Alerting
- Haversine formula for distance calculation
- Automatic routing to closest security booth
- GPS coordinate-based incident mapping
- Optimized response time through proximity routing

### Agentic Flow Design
- Autonomous incident classification
- Smart priority assignment
- Automated alert routing
- Self-learning behavior patterns

## 🌐 Access Information

### Application URLs
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs (FastAPI auto-generated)
- **Health Check**: http://localhost:8001/api/health

### How to start
cd backend -> python server.py
cd frontend -> npm install -> npm start

### Service Status
- **Frontend**: ✅ React development server running
- **Backend**: ✅ FastAPI server with all endpoints active
- **Database**: ✅ MongoDB connected and storing data
- **WebSocket**: ✅ Real-time communication established

## 🔮 Next Steps for Enhancement

### Advanced AI Features
- Integration with more sophisticated ML models
- Facial recognition for person identification
- Weapon detection capabilities
- Crowd density analysis

### Extended Monitoring
- Mobile app for security personnel
- Email/SMS notification integration
- Integration with existing campus security systems
- Analytics dashboard with historical reporting

### Scalability Improvements
- Multi-campus support
- Cloud deployment capabilities
- Load balancing for high-traffic scenarios
- Advanced caching and performance optimization

---

**The Watcher** represents a complete, production-ready university monitoring solution that combines cutting-edge AI technology with practical security needs, providing a comprehensive platform for campus safety and incident management.
