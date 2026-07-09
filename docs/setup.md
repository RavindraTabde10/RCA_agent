# Setup Guide

## Prerequisites

### System Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.9 or higher
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 1GB free space

### Required Software
- Python 3.9+
- pip package manager
- Git (optional)
- Virtual environment tool

## Installation Steps

### 1. Environment Setup

#### Create Virtual Environment

**Windows**:
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configuration

#### Create Configuration Files

```bash
# Copy example configs
copy config\config.yaml.example config\config.yaml
copy .env.example .env
```

#### Edit Configuration

**config/config.yaml**:
```yaml
app:
  name: "RCA Agent"
  log_level: "INFO"

llm:
  provider: "openai"
  model: "gpt-4"
```

**.env**:
```
LLM_API_KEY=your_api_key_here
JIRA_API_TOKEN=your_token_here
```

### 4. Directory Structure

Create required directories:
```bash
mkdir logs
mkdir output
mkdir data\knowledge_base
mkdir data\historical_defects
```

### 5. Verify Installation

```bash
python -c "import src; print('Installation successful!')"
```

## Integration Setup

### JIRA Integration

1. Generate API token:
   - Go to Atlassian Account Settings
   - Security → Create API token
   - Copy token

2. Configure in `.env`:
   ```
   JIRA_URL=https://your-company.atlassian.net
   JIRA_API_TOKEN=your_token
   JIRA_USER_EMAIL=your.email@company.com
   ```

3. Enable in `config.yaml`:
   ```yaml
   integrations:
     jira:
       enabled: true
   ```

### Git Integration

1. Configure repository path:
   ```yaml
   integrations:
     git:
       enabled: true
       repo_path: "/path/to/repo"
   ```

### LLM Setup

#### OpenAI
1. Get API key from https://platform.openai.com
2. Set in `.env`:
   ```
   LLM_API_KEY=sk-...
   LLM_PROVIDER=openai
   ```

#### Azure OpenAI
```
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
```

## Testing Setup

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure you're in virtual environment
pip list

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Configuration Errors**:
- Check YAML syntax
- Verify environment variables
- Ensure file paths are correct

**Permission Errors**:
- Run with appropriate permissions
- Check file/directory permissions

## Next Steps

1. Review [User Guide](user_guide.md)
2. Run example analysis
3. Configure integrations
4. Customize agents

## Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Email: support@example.com
