# User Guide

## Getting Started

### Basic Workflow

1. **Prepare Defect Data**
2. **Run Analysis**
3. **Review Diagnosis**
4. **Take Action**

## Analyzing a Defect

### Method 1: Python API

```python
from src.main import RCAAgent

# Create agent
agent = RCAAgent()

# Prepare defect data
defect = {
    "id": "BUG-123",
    "title": "Application crashes on startup",
    "description": "The app crashes when launched on Windows 10",
    "severity": "high",
    "logs": [
        "ERROR: Failed to initialize database connection",
        "java.sql.SQLException: Connection refused"
    ],
    "timestamp": "2026-07-09T10:00:00Z"
}

# Analyze
diagnosis = agent.analyze_defect(defect)

# Print results
print(f"Root Cause: {diagnosis['root_cause']}")
print(f"Confidence: {diagnosis['confidence']:.1%}")
print(f"Team: {diagnosis['assigned_team']}")
```

### Method 2: JIRA Integration

```python
from src.integrations.jira_integration import JiraIntegration
from src.main import RCAAgent

# Connect to JIRA
jira = JiraIntegration("https://your-jira.atlassian.net")
jira.connect()

# Fetch issue
issue = jira.get_issue("BUG-456")

# Analyze
agent = RCAAgent()
diagnosis = agent.analyze_defect(issue)

# Update JIRA
jira.update_issue("BUG-456", diagnosis)
```

## Understanding Results

### Diagnosis Structure

```python
{
    "defect_id": "BUG-123",
    "root_cause": "Database connection pool exhausted",
    "confidence": 0.85,
    "impact": {
        "severity": "high",
        "affected_users": "all",
        "business_impact": "critical"
    },
    "recommendations": [
        "Increase connection pool size",
        "Implement connection timeout",
        "Add retry logic"
    ],
    "assigned_team": "Backend Engineering",
    "priority": "high",
    "evidence": [...],
    "reasoning_steps": [...]
}
```

### Confidence Levels

- **High (80-100%)**: Strong evidence supporting diagnosis
- **Medium (50-79%)**: Moderate confidence, may need verification
- **Low (<50%)**: Uncertain diagnosis, manual investigation recommended

## Advanced Usage

### Custom Agent Configuration

```python
# Configure specific agents
config = {
    "agents": {
        "log_agent": {"enabled": True},
        "code_agent": {"enabled": False},
        "pattern_agent": {"enabled": True}
    }
}

agent = RCAAgent(config=config)
```

### Batch Analysis

```python
defects = [defect1, defect2, defect3]

results = []
for defect in defects:
    diagnosis = agent.analyze_defect(defect)
    results.append(diagnosis)
```

### Custom Reports

```python
from src.output_layer.diagnosis_generator import DiagnosisGenerator

generator = DiagnosisGenerator()

# Generate markdown report
report = generator.format_report(diagnosis, format_type="markdown")

# Save to file
with open("report.md", "w") as f:
    f.write(report)
```

## Best Practices

### Input Data Quality

1. **Provide Complete Information**:
   - Detailed description
   - Reproduction steps
   - Environment details
   - Error logs

2. **Include Context**:
   - When did it start?
   - What changed recently?
   - How often does it occur?

3. **Add Relevant Logs**:
   - Error messages
   - Stack traces
   - System logs

### Interpreting Results

1. **Check Confidence Score**:
   - High confidence → Likely accurate
   - Low confidence → Verify manually

2. **Review Evidence**:
   - Look at supporting data
   - Check reasoning steps

3. **Consider Recommendations**:
   - Prioritize by impact
   - Test in non-production first

### Team Assignment

The system assigns defects based on:
- Keywords in description
- Root cause type
- Component affected
- Team expertise

You can override automated assignment if needed.

## Troubleshooting

### Low Confidence Diagnoses

**Possible Reasons**:
- Insufficient data
- Uncommon defect pattern
- Conflicting evidence

**Solutions**:
- Provide more context
- Add detailed logs
- Include reproduction steps

### Incorrect Diagnosis

**What to Do**:
1. Review input data quality
2. Check agent configuration
3. Provide feedback for learning
4. Manual investigation

### Integration Issues

**JIRA Connection Failed**:
- Verify API token
- Check network connectivity
- Confirm JIRA URL

**Git Analysis Failed**:
- Verify repository path
- Check file permissions
- Ensure Git is installed

## Tips and Tricks

### Improve Accuracy

1. **Use Historical Data**: Feed past defects for pattern learning
2. **Detailed Logs**: Include timestamps and full stack traces
3. **Environment Info**: Specify OS, version, configuration

### Faster Analysis

1. **Disable Unused Agents**: Turn off agents you don't need
2. **Cache Results**: Enable caching for repeated analyses
3. **Parallel Processing**: Process multiple defects concurrently

### Better Reports

1. **Custom Templates**: Create report templates
2. **Export Formats**: Use markdown for documentation
3. **Evidence Inclusion**: Include full evidence trail

## Examples

See `examples/` directory for:
- Basic analysis examples
- Integration examples
- Custom configuration examples
- Batch processing examples

## FAQ

**Q: How long does analysis take?**
A: Typically 30-60 seconds per defect.

**Q: Can I analyze defects offline?**
A: Yes, if not using LLM features or online integrations.

**Q: How accurate is the diagnosis?**
A: 85-95% accuracy on common defect patterns.

**Q: Can I customize the agents?**
A: Yes, through configuration files and custom agents.

## Support

- Documentation: `docs/`
- Examples: `examples/`
- Issues: GitHub Issues
