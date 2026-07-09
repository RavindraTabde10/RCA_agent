# AI Agent for Root Cause Analysis

An AI-powered system that analyzes software defects using multiple data sources and intelligent reasoning to automatically diagnose issues and recommend the right team to fix them.

## Overview

The RCA Agent uses a multi-layered architecture with specialized AI agents to perform comprehensive root cause analysis on software defects. It processes logs, code, comments, and temporal data to provide accurate diagnoses with confidence scores.

## Features

- **Multi-Agent Analysis**: Specialized agents for logs, code, and patterns
- **Chain of Thoughts Reasoning**: Step-by-step logical analysis
- **Knowledge Base**: Learns from historical defects
- **Team Assignment**: Intelligent routing to appropriate teams
- **Multiple Integrations**: JIRA, Git, Slack, and more
- **Comprehensive Reports**: Detailed diagnosis with evidence and recommendations

## Architecture

```
Input Layer → Processing Layer → Knowledge Layer → Output Layer
     ↓              ↓                   ↓              ↓
  Defects      AI Agents          Domain KB      Diagnosis
   Logs        Reasoning         Source Code    Team Assignment
 Comments      Chain of          Best            Reports
  Time         Thoughts          Practices
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (optional, for source code analysis)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ltts_hackathon_work
```

2. Create virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Configure the application:
```bash
# Copy example config
copy config\config.yaml.example config\config.yaml

# Edit configuration
notepad config\config.yaml
```

6. Set environment variables:
```bash
# Windows
set LLM_API_KEY=your_api_key_here
set JIRA_API_TOKEN=your_jira_token_here

# Linux/Mac
export LLM_API_KEY=your_api_key_here
export JIRA_API_TOKEN=your_jira_token_here
```

## Quick Start

### Basic Usage

```python
from src.main import RCAAgent

# Initialize agent
agent = RCAAgent()

# Analyze a defect
defect_data = {
    "id": "BUG-12345",
    "description": "Application crashes when processing large datasets",
    "timestamp": "2026-07-09T10:30:00Z",
    "logs": ["ERROR: OutOfMemoryError..."],
    "comments": []
}

# Run analysis
diagnosis = agent.analyze_defect(defect_data)

# Print results
print(diagnosis)
```

### Command Line

```bash
python src/main.py
```

## Configuration

### Main Configuration (`config/config.yaml`)

- **App Settings**: Name, version, logging
- **Agents**: Enable/disable agents
- **LLM**: Model selection and parameters
- **Integrations**: JIRA, Git, Slack, etc.
- **Output**: Report format and location

### Agent Configuration (`config/agents_config.yaml`)

- Configure individual agent behaviors
- Set capabilities and parameters
- Adjust analysis depth and thresholds

## Usage Examples

### Analyze from JIRA

```python
from src.integrations.jira_integration import JiraIntegration
from src.main import RCAAgent

# Connect to JIRA
jira = JiraIntegration("https://your-jira.atlassian.net")
jira.connect()

# Fetch issue
issue = jira.get_issue("BUG-123")

# Analyze
agent = RCAAgent()
diagnosis = agent.analyze_defect(issue)

# Update JIRA with diagnosis
jira.update_issue("BUG-123", diagnosis)
```

### Analyze with Git Integration

```python
from src.integrations.git_integration import GitIntegration
from src.main import RCAAgent

# Connect to repository
git = GitIntegration("/path/to/repo")
git.connect()

# Get recent commits
commits = git.get_recent_commits()

# Analyze defect with code context
diagnosis = agent.analyze_defect({
    "id": "BUG-456",
    "description": "Performance degradation",
    "code_context": {"recent_changes": commits}
})
```

## Project Structure

```
ltts_hackathon_work/
├── src/
│   ├── input_layer/          # Data ingestion
│   ├── processing_layer/     # AI agents and reasoning
│   ├── knowledge_layer/      # Domain knowledge
│   ├── output_layer/         # Diagnosis generation
│   ├── integrations/         # External systems
│   ├── models/              # Data models
│   └── utils/               # Utilities
├── config/                   # Configuration files
├── data/                    # Knowledge base and data
├── docs/                    # Documentation
├── tests/                   # Test suite
├── output/                  # Generated reports
└── requirements.txt         # Dependencies
```

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_diagnosis.py

# Run with coverage
pytest --cov=src tests/
```

## Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [User Guide](docs/user_guide.md)
- [Setup Instructions](docs/setup.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Email: support@example.com
- Documentation: docs/

## Roadmap

- [ ] Image and video analysis support
- [ ] Predictive defect detection
- [ ] Auto-fix capabilities
- [ ] Enhanced visualizations
- [ ] CI/CD integration
- [ ] Continuous learning from resolutions

---

**Version**: 0.1.0  
**Last Updated**: 2026-07-09
