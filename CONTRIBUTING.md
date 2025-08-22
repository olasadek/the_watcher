# Contributing to The Watcher

We welcome contributions to The Watcher! This document provides guidelines for contributing to this university security monitoring system.

## 🎯 Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a new branch for your feature
4. **Make** your changes
5. **Test** your changes thoroughly
6. **Submit** a pull request

## 🛠️ Development Setup

### Prerequisites
- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- MongoDB 4.4+
- Git

### Local Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/the_watcher.git
cd the_watcher

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up frontend
cd ../frontend
npm install

# Start MongoDB (ensure it's running on localhost:27017)
```

## 📝 Contribution Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints where possible
- Maximum line length: 100 characters
- Use descriptive variable and function names

```python
# Good
def analyze_crowd_density(frame: np.ndarray) -> Dict[str, Any]:
    """Analyze crowd density in the given frame."""
    pass

# Bad
def analyze(f):
    pass
```

#### JavaScript/React (Frontend)
- Use functional components with hooks
- Follow ESLint configuration
- Use camelCase for variables and functions
- Use descriptive component names

```javascript
// Good
const CrowdAnalysisComponent = ({ crowdData }) => {
    const [isLoading, setIsLoading] = useState(false);
    // ...
};

// Bad
const comp = ({ data }) => {
    // ...
};
```

### Testing Requirements

#### Backend Tests
- Add tests for new AI detection algorithms
- Test API endpoints thoroughly
- Include edge cases and error conditions

```bash
# Run backend tests
cd backend
python -m pytest test_crowd_analysis.py -v
```

#### Frontend Tests
- Add tests for new React components
- Test user interactions and API calls
- Ensure accessibility compliance

```bash
# Run frontend tests
cd frontend
npm test
```

### Commit Messages

Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(crowd-analysis): add density threshold configuration
fix(camera): resolve webcam permission issues on Chrome
docs(readme): update installation instructions
```

## 🚀 Feature Development

### Adding New AI Detection Features

1. **Create detection algorithm** in `backend/vision_analyzer.py`
2. **Add API endpoint** in `backend/server.py`
3. **Create frontend component** in `frontend/src/`
4. **Add tests** for your detection algorithm
5. **Update documentation**

Example structure:
```python
# In vision_analyzer.py
def detect_new_incident_type(self, frame: np.ndarray) -> Dict[str, Any]:
    """Detect new type of security incident."""
    # Implementation here
    return {
        "incident_type": "new_type",
        "confidence": 0.85,
        "location": {"x": 100, "y": 200},
        "timestamp": datetime.now().isoformat()
    }
```

### Adding New University Templates

1. **Define university configuration** in `frontend/src/UniversityConfig.js`
2. **Add GPS coordinates** for campus locations
3. **Configure camera and booth positions**
4. **Test with real campus layout**

### Extending Mapping Features

1. **Enhance map functionality** in `frontend/src/RealMap.js`
2. **Add new marker types** or interactions
3. **Integrate with additional mapping services**
4. **Test GPS coordinate accuracy**

## 🐛 Bug Reports

### Before Submitting
- Check existing issues for duplicates
- Test with the latest version
- Provide minimal reproduction steps

### Bug Report Template
```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Environment**
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Python Version: [e.g. 3.9.7]
- Node.js Version: [e.g. 18.12.0]
- Browser: [e.g. Chrome 96, Firefox 95]

**Additional Context**
Screenshots, error logs, etc.
```

## 💡 Feature Requests

### Template
```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Explain why this feature would be useful.

**Proposed Implementation**
Your ideas on how this could be implemented.

**Additional Context**
Any other relevant information.
```

## 🔍 Code Review Process

### For Contributors
- Ensure all tests pass
- Follow code style guidelines
- Include documentation updates
- Respond to review feedback promptly

### For Reviewers
- Focus on functionality and security
- Suggest improvements constructively
- Test changes locally when possible
- Approve when satisfied with quality

## 🎨 UI/UX Contributions

### Design Guidelines
- Follow existing dark security theme
- Maintain accessibility standards (WCAG 2.1)
- Ensure responsive design
- Use Lucide React icons consistently

### Tailwind CSS Usage
- Use existing utility classes
- Follow component-based styling
- Maintain consistent spacing and colors

## 🔒 Security Considerations

### When Contributing
- Never commit sensitive data (API keys, passwords)
- Follow secure coding practices
- Report security vulnerabilities privately
- Test for common security issues

### Security Review
All security-related changes undergo additional review:
- Input validation and sanitization
- Authentication and authorization
- Data encryption and privacy
- Dependency security updates

## 📚 Documentation

### Required Documentation
- Update README.md for new features
- Add inline code comments
- Include API documentation
- Update user guides

### Documentation Style
- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Keep documentation up-to-date

## 🏷️ Release Process

### Versioning
We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Steps
1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Deploy to production

## 🤝 Community

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Maintain professional communication

## 🎓 Learning Resources

### For New Contributors
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [MongoDB Python Tutorial](https://pymongo.readthedocs.io/en/stable/tutorial.html)

### Project-Specific Knowledge
- Computer vision and AI detection algorithms
- University security best practices
- Real-time web application architecture
- GPS mapping and coordinate systems

## 📈 Metrics and Analytics

### Contribution Metrics
We track:
- Code quality improvements
- Bug fix response time
- Feature adoption rates
- Community engagement

### Recognition
Contributors are recognized through:
- GitHub contributor stats
- Release notes mentions
- Project documentation credits

## 🚀 Future Roadmap

### Planned Features
- Mobile application development
- Advanced AI model integration
- Multi-language support
- Cloud deployment options

### How to Influence Roadmap
- Submit detailed feature requests
- Contribute proof-of-concept implementations
- Participate in roadmap discussions
- Provide user feedback and use cases

---

Thank you for contributing to The Watcher! Your efforts help improve university security systems worldwide. 🙏
