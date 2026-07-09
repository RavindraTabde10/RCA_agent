# Azure OpenAI LLM Integration Guide

## Overview

The RCA Agent now uses Azure OpenAI for intelligent root cause analysis. LLM capabilities are integrated into:
- **Code Agent**: Analyzes code for bugs and issues
- **Log Agent**: Analyzes errors and exceptions
- **Pattern Agent**: Identifies similar defects
- **Hypothesis Generator**: Generates sophisticated hypotheses
- **Chain of Thoughts**: Synthesizes conclusions

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements_rca.txt
```

This installs the OpenAI Python SDK (version 1.0.0+) which supports Azure OpenAI.

### 2. Configure Environment Variables

Create a `.env` file in the project root with your Azure OpenAI credentials:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_team_key_here
AZURE_OPENAI_ENDPOINT=https://your-apim.azure-api.net
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_MODEL=gpt-4
```

**Where to get these values:**
- `AZURE_OPENAI_API_KEY`: Your team's API key (from onboarding)
- `AZURE_OPENAI_ENDPOINT`: Your Azure API Management endpoint
- `AZURE_OPENAI_API_VERSION`: API version (use the one from onboarding)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Name of your deployed model
- `AZURE_OPENAI_MODEL`: The model name (e.g., gpt-4, gpt-3.5-turbo)

### 3. Test the Integration

Run the test script to verify your setup:

```bash
python test_llm_integration.py
```

Expected output:
```
================================================================================
Testing Azure OpenAI LLM Integration
================================================================================

1. Checking environment variables...
   ✓ AZURE_OPENAI_API_KEY: abcd1234...xyz9
   ✓ AZURE_OPENAI_ENDPOINT: https://your-apim.azure-api.net
   ✓ AZURE_OPENAI_API_VERSION: 2024-02-15-preview
   ✓ AZURE_OPENAI_DEPLOYMENT_NAME: gpt-4

2. Initializing LLM client...
   ✓ LLM client initialized successfully

3. Testing chat completion...
   ✓ Chat completion successful
   Response: Four

4. Testing RCA analysis...
   ✓ RCA analysis successful
   Analysis: The NullPointerException indicates that...

================================================================================
✅ All tests passed! Your LLM integration is working correctly.
================================================================================
```

## Usage in Code

### Using the LLM Client Directly

```python
from src.utils.llm_client import get_llm_client

# Get LLM client (singleton)
llm_client = get_llm_client()

# Simple text analysis
response = llm_client.analyze_text(
    prompt="Explain this error: NullPointerException",
    system_message="You are a debugging expert.",
    temperature=0.3
)
print(response)

# Chat completion with custom messages
response = llm_client.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What causes a memory leak?"}
    ],
    temperature=0.5
)
print(response["content"])
```

### Using Agents with LLM

```python
from src.processing_layer.agents.code_agent import CodeAgent
from src.processing_layer.agents.log_agent import LogAgent
from src.utils.config import load_config

# Load configuration
config = load_config()
llm_config = config.get("llm", {})

# Initialize agents
code_agent = CodeAgent(llm_config=llm_config)
log_agent = LogAgent(llm_config=llm_config)

# Analyze code
code_context = {
    "files": [
        {
            "path": "UserService.java",
            "content": "public class UserService { ... }"
        }
    ]
}
results = code_agent.analyze(code_context, defect_context)
print(results)
```

## Configuration Options

### In config.yaml

```yaml
llm:
  provider: "azure_openai"
  azure_endpoint: "${AZURE_OPENAI_ENDPOINT}"
  api_key: "${AZURE_OPENAI_API_KEY}"
  api_version: "${AZURE_OPENAI_API_VERSION}"
  deployment_name: "${AZURE_OPENAI_DEPLOYMENT_NAME}"
  model: "${AZURE_OPENAI_MODEL}"
  temperature: 0.7        # Creativity level (0.0-1.0)
  max_tokens: 2000        # Maximum response length
```

### Temperature Settings

- **0.0-0.3**: Deterministic, focused responses (best for code analysis)
- **0.4-0.7**: Balanced creativity (good for hypotheses)
- **0.8-1.0**: More creative responses (use sparingly)

## Architecture

### LLM Client (`src/utils/llm_client.py`)

The `LLMClient` class provides a centralized interface to Azure OpenAI:

```python
class LLMClient:
    def __init__(self, config: Dict[str, Any])
    def chat_completion(messages: List[Dict], **kwargs) -> Dict
    def analyze_text(prompt: str, system_message: str, **kwargs) -> str
    def analyze_with_context(question: str, context: str, **kwargs) -> str
```

**Singleton Pattern**: Use `get_llm_client(config)` to get a shared instance.

### Agent Integration

Each agent now includes LLM-powered analysis:

1. **Code Agent**
   - Analyzes code structure using LLM
   - Generates specific recommendations
   - Temperature: 0.3 (focused)

2. **Log Agent**
   - Analyzes error messages
   - Interprets stack traces
   - Temperature: 0.3 (focused)

3. **Pattern Agent**
   - Finds semantically similar defects
   - Temperature: 0.3 (focused)

4. **Hypothesis Generator**
   - Generates sophisticated hypotheses
   - Temperature: 0.6 (balanced)

5. **Chain of Thoughts**
   - Synthesizes final conclusions
   - Temperature: 0.4 (slightly creative)

## Troubleshooting

### Error: "API key is required"

**Solution**: Ensure `.env` file has `AZURE_OPENAI_API_KEY` set correctly.

```bash
# Check if .env exists
ls -la .env

# Load environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AZURE_OPENAI_API_KEY'))"
```

### Error: "Failed to initialize Azure OpenAI client"

**Possible causes:**
1. Invalid API key
2. Wrong endpoint URL
3. Network connectivity issues

**Solution**: Run the test script for detailed diagnostics:
```bash
python test_llm_integration.py
```

### Error: "DeploymentNotFound"

**Solution**: Check that `AZURE_OPENAI_DEPLOYMENT_NAME` matches your actual deployment name in Azure.

### Rate Limiting

If you encounter rate limit errors:
1. Reduce the number of concurrent requests
2. Add retry logic with exponential backoff
3. Contact your Azure admin to increase quota

## Best Practices

1. **Error Handling**: All LLM calls are wrapped in try-except blocks
2. **Fallback Logic**: Agents work without LLM if initialization fails
3. **Context Length**: Code/logs are truncated to prevent token limit errors
4. **JSON Parsing**: LLM responses are validated before use
5. **Logging**: All LLM interactions are logged for debugging

## Security Notes

- ⚠️ Never commit `.env` file to version control
- ⚠️ API keys should be stored securely
- ✓ Use environment variables for sensitive data
- ✓ The `.env.example` file is safe to commit (no actual keys)

## Performance Considerations

### Token Usage

- Average tokens per code analysis: 500-1500
- Average tokens per log analysis: 300-1000
- Average tokens per hypothesis: 400-800

### Response Time

- Simple queries: 1-3 seconds
- Complex analysis: 3-8 seconds
- Parallel agent execution helps minimize total time

## Advanced Usage

### Custom LLM Configuration per Agent

```python
# Different configs for different agents
code_agent_config = {
    "temperature": 0.2,  # More deterministic
    "max_tokens": 1500
}

hypothesis_config = {
    "temperature": 0.7,  # More creative
    "max_tokens": 2500
}

code_agent = CodeAgent(llm_config=code_agent_config)
hypothesis_gen = HypothesisGenerator(llm_config=hypothesis_config)
```

### Monitoring Token Usage

```python
response = llm_client.chat_completion(messages)
print(f"Tokens used: {response['usage']['total_tokens']}")
```

## Support

For issues or questions:
1. Check this documentation
2. Run `test_llm_integration.py` for diagnostics
3. Check logs in `logs/rca_agent.log`
4. Review Azure OpenAI documentation

## References

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Best Practices for Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
