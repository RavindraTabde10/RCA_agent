# Jira Bug Fetcher

A Python script to fetch and display bug details from Jira using the REST API.

## Features

- ✅ Fetch all bugs from a specific project
- ✅ Get details of specific issues
- ✅ Search using custom JQL queries
- ✅ Export results to JSON
- ✅ Formatted console output
- ✅ Environment variable configuration

## Prerequisites

- Python 3.7 or higher
- Jira API token
- Access to a Jira instance

## Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Get Your Jira API Token

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Python Automation")
4. Copy the generated token (you won't see it again!)

### 3. Configure Environment Variables

Create a `.env` file in the project directory:

```powershell
cp .env.example .env
```

Edit the `.env` file and add your credentials:

```
JIRA_URL=https://ravindratabde10.atlassian.net
JIRA_EMAIL=your-email@gmail.com
JIRA_API_TOKEN=your_api_token_here
PROJECT_KEY=KAN
```

⚠️ **Important**: Never commit the `.env` file with your actual credentials!

## Usage

### Basic Usage - Fetch All Bugs

```powershell
python jira_automation.py
```

This will:
- Fetch all bugs from your project
- Display them in the console
- Save results to `jira_bugs.json`

### API Endpoints Available

The script includes a `JiraClient` class with the following methods:

#### Get All Projects
```python
from jira_automation import JiraClient

client = JiraClient(jira_url, email, api_token)
projects = client.get_all_projects()
```

#### Get Specific Issue
```python
issue = client.get_issue('KAN-123')
```

#### Search Bugs in Project
```python
result = client.search_bugs(project_key='KAN', max_results=50)
```

#### Custom JQL Query
```python
# Search for open high-priority bugs
jql = "project = KAN AND issuetype = Bug AND status != Done AND priority = High"
result = client.search_with_jql(jql, max_results=100)
```

#### Get Board Issues
```python
# Board ID can be found in your Jira board URL
issues = client.get_board_issues(board_id=1)
```

## Example Output

```
Connecting to Jira: https://ravindratabde10.atlassian.net

Fetching bugs from project: KAN

Found 15 bug(s) in project KAN
Displaying 15 bug(s)

================================================================================
Issue Key: KAN-42
Summary: Login button not working on mobile
Status: In Progress
Priority: High
Assignee: John Doe
Reporter: Jane Smith
Created: 2026-07-08T10:30:45.123+0000
Updated: 2026-07-09T08:15:22.456+0000
Description: [Rich content - view in Jira]
================================================================================

✓ Full results saved to jira_bugs.json
```

## Common JQL Queries

```python
# All bugs in project
"project = KAN AND issuetype = Bug"

# Open bugs only
"project = KAN AND issuetype = Bug AND status != Done"

# High priority bugs
"project = KAN AND issuetype = Bug AND priority = High"

# Bugs created today
"project = KAN AND issuetype = Bug AND created >= startOfDay()"

# Unassigned bugs
"project = KAN AND issuetype = Bug AND assignee is EMPTY"

# Bugs assigned to me
"project = KAN AND issuetype = Bug AND assignee = currentUser()"
```

## Jira API Documentation

- REST API v3: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- JQL Reference: https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/

## Troubleshooting

### Authentication Error (401)
- Verify your email and API token are correct
- Make sure the API token hasn't expired
- Check if you have access to the Jira instance

### Permission Error (403)
- Verify you have permission to view the project
- Check if the project key is correct

### Not Found Error (404)
- Verify the Jira URL is correct
- Check if the project/issue exists

## Advanced Usage

### Custom Script Example

```python
from jira_automation import JiraClient
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize client
client = JiraClient(
    os.getenv('JIRA_URL'),
    os.getenv('JIRA_EMAIL'),
    os.getenv('JIRA_API_TOKEN')
)

# Get all open bugs
result = client.search_with_jql(
    "project = KAN AND issuetype = Bug AND status = 'To Do'",
    max_results=100
)

# Process results
for issue in result['issues']:
    print(f"{issue['key']}: {issue['fields']['summary']}")
```

## Security Notes

- ⚠️ Never commit your `.env` file with actual credentials
- 🔒 Store API tokens securely
- 🔄 Rotate API tokens regularly
- 🚫 Don't share tokens in code or logs

## License

MIT License - feel free to use and modify for your projects.
