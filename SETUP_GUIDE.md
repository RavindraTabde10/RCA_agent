# RCA Agent - Setup Guide

## Quick Setup (5 Minutes)

### Step 1: Copy Project Folder
Copy the entire `RCA_agent-main` folder to your new PC.

### Step 2: Install Python
1. Download Python 3.9+ from https://www.python.org/downloads/
2. During installation, **CHECK "Add Python to PATH"**
3. Verify: Open Command Prompt/PowerShell and run:
   ```cmd
   python --version
   ```

### Step 3: Install Dependencies
Open PowerShell/Terminal in the project folder:

```powershell
cd path\to\RCA_agent-main

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements_rca.txt
```

### Step 4: Create Environment File
Create `.env` file in the project root with your credentials:

```bash
# === JIRA Configuration ===
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=YOUR_PROJECT

# === LLM Configuration (Choose ONE) ===

# Option A: Azure OpenAI (Recommended for Enterprise)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Option B: OpenAI
# OPENAI_API_KEY=sk-your-openai-key

# Option C: Custom LLM Endpoint
# LLM_ENDPOINT_URL=http://localhost:11434/v1
# LLM_API_KEY=not-required
```

### Step 5: Update Config
Edit `config/config.yaml`:

```yaml
llm:
  provider: "azure_openai"  # or "openai" or "custom"
```

---

## Test Your Setup

### 1. Run Local Test (No JIRA needed)
```powershell
python test_local_rca.py
```

Expected output:
```
============================================================
   RCA AGENT - LOCAL TEST
============================================================
TEST 1: DLT File Parsing ✅ PASS
TEST 2: Domain Knowledge ✅ PASS
TEST 3: RCA Analysis ✅ PASS
🎉 ALL TESTS PASSED - Ready to deploy!
```

### 2. View Generated Report
After test, open:
```
output/reports/TEST-001_rca.html
```

---

## Folder Structure

```
RCA_agent-main/
├── .env                      # YOUR CREDENTIALS (create this)
├── config/
│   └── config.yaml           # Main configuration
├── data/
│   ├── defects/              # Local defect JSON files
│   ├── dlt_logs/             # DLT log files for testing
│   └── knowledge_base/
│       └── domain_knowledge/ # 7 knowledge MD files
├── output/
│   ├── reports/              # Generated RCA reports
│   └── tickets/              # Per-ticket workspaces
├── src/
│   └── rca_infotainment/     # Core RCA engine
├── jira_data_fetcher.py      # JIRA API utility
├── rca_scheduler.py          # Automated RCA scheduler  
├── test_local_rca.py         # Local testing script
└── requirements_rca.txt      # Python dependencies
```

---

## Running the RCA Agent

### Option 1: Manual Single Ticket
```powershell
# Analyze local defect
python -c "
from src.rca_infotainment.rca_engine import RCAEngine
from src.utils.config import load_config

config = load_config('config/config.yaml')
engine = RCAEngine(config)
result = engine.analyze_defect('TEST-001', from_jira=False)
print(f'Root Cause: {result.get(\"root_cause\", \"N/A\")[:200]}')
"
```

### Option 2: Automated Scheduler (Fetch from JIRA)
```powershell
# Single run - fetch tickets with 'needs-rca' label
python rca_scheduler.py

# Continuous daemon mode (every 5 minutes)
python rca_scheduler.py --daemon --interval 300

# Test mode (no JIRA updates)
python rca_scheduler.py --dry-run
```

### Option 3: JIRA Fetch Utility
```powershell
# Fetch single ticket
python jira_data_fetcher.py --ticket SAM1-123 --download-dir ./attachments

# Fetch by labels
python jira_data_fetcher.py --labels needs-rca,auto-rca
```

---

## Windows Task Scheduler Setup

For fully automated operation:

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task → Name: "RCA Agent"
3. Trigger: Daily or every X hours
4. Action: Start a program
   - Program: `python.exe` (full path)
   - Arguments: `rca_scheduler.py`
   - Start in: `C:\path\to\RCA_agent-main`
5. Finish

Or use the batch file:
```powershell
run_rca_scheduler.bat
```

---

## Troubleshooting

### "Module not found" Error
```powershell
# Ensure you're in the project directory
cd RCA_agent-main

# Reinstall dependencies
pip install -r requirements_rca.txt
```

### "JIRA authentication failed"
1. Check `.env` credentials are correct
2. Generate new API token: https://id.atlassian.com/manage-profile/security/api-tokens
3. Use your Atlassian email (not username)

### "LLM not available"
1. Check API key in `.env`
2. Verify endpoint URL is correct
3. Test with: `python test_llm_integration.py`

### "No knowledge loaded"
Verify knowledge files exist:
```powershell
ls data/knowledge_base/domain_knowledge/
```
Should show 7 `.md` files.

---

## Quick Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements_rca.txt`)
- [ ] `.env` file created with credentials
- [ ] `python test_local_rca.py` passes
- [ ] Reports generated in `output/reports/`

---

## Contact

For issues: Check logs in `logs/` folder at `logs/rca_scheduler.log`
```powershell
# Run in test mode to see issues without updating JIRA
python rca_scheduler.py --dry-run
```
