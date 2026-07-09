# 🚀 Quick Start Guide - Jira Automation

Get started with Jira automation in 5 minutes!

## Step 1: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `requests` - for HTTP API calls
- `python-dotenv` - for environment variable management

## Step 2: Create Your .env File

Copy the example file and add your credentials:

```powershell
copy .env.example .env
```

Edit `.env` and add:
```
JIRA_URL=https://ravindratabde10.atlassian.net
JIRA_EMAIL=ravindra.tabde10@gmail.com
JIRA_API_TOKEN=YOUR_ACTUAL_TOKEN_HERE
PROJECT_KEY=KAN
```

### Get Your API Token:
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it (e.g., "Python Automation")
4. Copy the token and paste it in your .env file

## Step 3: Verify Setup

```powershell
python setup_check.py
```

This will verify:
- ✅ Dependencies are installed
- ✅ .env file is configured
- ✅ Connection to Jira works

## Step 4: Run the Scripts!

### Basic Usage - Fetch All Bugs

```powershell
python jira_automation.py
```

Output: Console display + `jira_bugs.json` file

### Advanced Operations

```powershell
python jira_operations.py
```

This runs multiple analyses:
- Bug statistics
- Open bugs
- High priority bugs
- Unassigned bugs
- Recently created bugs
- CSV export

## What You Get

### Files Created:
- **jira_automation.py** - Main script with JiraClient class
- **jira_operations.py** - Common operations and examples
- **setup_check.py** - Setup verification
- **jira_bugs.json** - Exported bug data
- **KAN_bugs_export.csv** - CSV export of all bugs

## Common Use Cases

### 1. Get Specific Issue Details
```python
from jira_automation import JiraClient
from dotenv import load_dotenv
import os

load_dotenv()
client = JiraClient(os.getenv('JIRA_URL'), os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))

issue = client.get_issue('KAN-123')
print(issue['fields']['summary'])
```

### 2. Custom JQL Search
```python
# Search for bugs created this week
result = client.search_with_jql(
    "project = KAN AND issuetype = Bug AND created >= startOfWeek()",
    max_results=50
)
```

### 3. Filter by Status
```python
# Get all 'In Progress' bugs
result = client.search_with_jql(
    "project = KAN AND issuetype = Bug AND status = 'In Progress'",
    max_results=100
)
```

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rest/api/3/project` | List all projects |
| GET | `/rest/api/3/issue/{key}` | Get specific issue |
| GET | `/rest/api/3/search?jql=...` | Search with JQL |
| GET | `/rest/agile/1.0/board/{id}/issue` | Get board issues |

## Troubleshooting

### "401 Unauthorized"
- Check your email and API token
- Token might be expired - create a new one

### "403 Forbidden"  
- Verify you have access to the project
- Check project key is correct

### "404 Not Found"
- Verify Jira URL is correct
- Check if project/issue exists

### Script runs but shows no bugs
- Project might not have any bugs
- Try: `python jira_operations.py` to see statistics

## Next Steps

1. ✅ Run `setup_check.py` to verify everything works
2. ✅ Run `jira_automation.py` to fetch bugs
3. ✅ Run `jira_operations.py` for detailed analysis
4. ✅ Customize scripts for your specific needs
5. ✅ Read README_JIRA.md for detailed documentation

## Security Reminder

- 🔒 Never commit `.env` file
- 🔒 Keep API tokens secure
- 🔒 Rotate tokens regularly
- 🔒 Use `.gitignore` to exclude sensitive files

## Need Help?

Check the detailed documentation:
- **README_JIRA.md** - Full documentation
- **Jira API Docs** - https://developer.atlassian.com/cloud/jira/platform/rest/v3/

---

**Ready to automate? Run `python setup_check.py` now!** 🎯
