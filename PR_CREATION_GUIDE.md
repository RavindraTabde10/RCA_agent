# GitHub PR Creation - Quick Start Guide

This guide shows how to enable automatic Pull Request creation when running the RCA scheduler.

## 🎯 What's New

The RCA scheduler (`rca_scheduler.py`) now supports **automatic GitHub Pull Request creation** for code fixes in impacted .cpp files!

When enabled, the scheduler will:
1. Analyze the defect using RCA
2. Identify impacted source files (.cpp, .h, etc.)
3. Generate code fixes based on root cause analysis
4. Create a GitHub Pull Request with the fixes
5. Update JIRA with the PR link

---

## ⚙️ Configuration

### Step 1: Enable PR Creation in Config

Edit `config/config.yaml` and ensure the `scheduler` section has `auto_create_pr: true`:

```yaml
scheduler:
  # Labels that trigger RCA
  trigger_labels:
    - "needs-rca"
    - "auto-rca"
    - "rca-requested"
  
  # Label added after successful RCA
  completion_label: "rca-complete"
  
  # Label added while analysis is running
  in_progress_label: "rca-in-progress"
  
  # Label added on failure
  error_label: "rca-error"
  
  # Max tickets to process per run
  max_tickets_per_run: 10
  
  # Additional JQL filter for tickets
  jql_filter: "status != Closed AND status != Done"
  
  # Remove trigger label after RCA completes
  remove_trigger_label: true
  
  # Upload MD/HTML reports to JIRA
  upload_to_jira: true
  
  # Link duplicate tickets
  mark_duplicates: true
  
  # 🆕 Automatically create GitHub PR with code fix
  auto_create_pr: true  # <-- SET THIS TO TRUE
```

### Step 2: Configure Git/GitHub Integration

Ensure your `.env` file has the following variables:

```bash
# GitHub Configuration (REQUIRED for PR creation)
GIT_REPO_URL=https://github.com/your-org/your-repo.git
GIT_TOKEN=ghp_YourGitHubPersonalAccessToken
GIT_BRANCH=main
GIT_USERNAME=your-github-username
GIT_LOCAL_PATH=./temp/repo_clone

# For GitHub Enterprise (optional)
GITHUB_ENTERPRISE_API_URL=https://github.yourcompany.com/api/v3
```

#### How to Get a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (all)
   - ✅ `workflow`
4. Copy the token (starts with `ghp_`)
5. Add to `.env` as `GIT_TOKEN=ghp_...`

---

## 🚀 Usage

### Run the Scheduler Once

Process all tickets with the trigger label and create PRs:

```bash
python rca_scheduler.py
```

Expected output:
```
RCA Scheduler initialized (dry_run=False)
Trigger labels: ['needs-rca', 'auto-rca', 'rca-requested']
Auto-create PR: True  # <-- Confirms PR creation is enabled
✓ Git service connected
✓ JIRA connected
✓ LLM service connected

Processing ticket: KAN-16
   Running analysis with automatic PR creation...
   ✓ GitHub PR created: https://github.com/your-org/your-repo/pull/123
   
✅ RCA completed for KAN-16
   Root Cause: USB source switch delay due to sequential initialization...
   Confidence: 85%
   GitHub PR: https://github.com/your-org/your-repo/pull/123
   PR Number: #123
```

### Run as Continuous Daemon

Run the scheduler every 5 minutes:

```bash
python rca_scheduler.py --daemon --interval 300
```

### Dry Run (Test Mode)

Test without actually creating PRs or updating JIRA:

```bash
python rca_scheduler.py --dry-run
```

---

## 🔍 What Gets Created

When a PR is created, it includes:

### 1. Branch Name
Format: `fix/{defect-id}-{sanitized-summary}`

Example: `fix/kan-16-usb-source-switch-delay`

### 2. PR Title
Format: `[{DEFECT-ID}] {Short description} - {Component}`

Example: `[KAN-16] Fix USB source switch delay - Optimize MediaService initialization`

### 3. PR Description
Includes:
- Root Cause Analysis summary
- Impacted files
- Proposed code changes
- Expected impact
- Link back to JIRA ticket

### 4. Changed Files
The PR will include fixes for:
- `.cpp` files with implementation changes
- `.h` files with header updates
- Related configuration files

---

## 📝 Example Workflow

### Scenario: Fix USB Source Switch Delay

1. **Tester adds label to JIRA ticket**
   ```
   Ticket: KAN-16
   Summary: USB source switch takes 378ms (target: <200ms)
   Label: needs-rca
   ```

2. **Scheduler picks it up automatically**
   ```bash
   python rca_scheduler.py
   ```

3. **RCA Analysis Runs**
   - Parses DLT logs
   - Maps errors to source code
   - Identifies root cause: Sequential initialization instead of parallel

4. **PR Created Automatically**
   ```
   Branch: fix/kan-16-usb-source-switch-delay
   PR #123: [KAN-16] Fix USB source switch delay - Optimize MediaService
   Files changed: audio/USBMediaHandler.cpp, audio/MediaService.h
   ```

5. **JIRA Updated**
   - Comment with RCA results added
   - Reports (MD/HTML) attached
   - Link to PR added
   - Labels updated: `needs-rca` → `rca-complete`

6. **Developer Reviews PR**
   - Reviews the automated code fix
   - Merges or requests changes
   - Original issue gets resolved faster!

---

## 🛠️ Troubleshooting

### PR Creation Fails

**Symptom**: Analysis completes but no PR is created

**Solutions**:

1. **Check Git connection**
   ```bash
   # Verify .env has correct values
   echo $GIT_REPO_URL
   echo $GIT_TOKEN
   ```

2. **Check token permissions**
   - Ensure token has `repo` and `workflow` scopes
   - For private repos, token must have access

3. **Check scheduler logs**
   ```bash
   tail -f logs/rca_scheduler.log
   ```
   Look for errors like:
   - `Git not connected - PR creation will fail!`
   - `Failed to create branch`
   - `Authentication failed`

### No Tickets Processed

**Symptom**: Scheduler runs but finds no tickets

**Solutions**:

1. **Verify JIRA labels**
   - Check tickets have label `needs-rca` (or your configured trigger label)
   - Verify tickets are not closed

2. **Check JIRA connection**
   ```bash
   # Verify .env has correct values
   echo $JIRA_URL
   echo $JIRA_EMAIL
   echo $JIRA_API_TOKEN
   ```

3. **Test with specific ticket**
   ```python
   # Test script
   from jira_data_fetcher import JiraDataFetcher
   
   jira = JiraDataFetcher(JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)
   tickets = jira.fetch_by_labels(['needs-rca'], project_key='KAN')
   print(f"Found {len(tickets)} tickets")
   ```

---

## 🎛️ Advanced Configuration

### Disable PR Creation Temporarily

Set `auto_create_pr: false` in `config/config.yaml`:

```yaml
scheduler:
  auto_create_pr: false  # Only run analysis, no PR
```

### Custom Trigger Labels

Use different labels for different workflows:

```yaml
scheduler:
  trigger_labels:
    - "needs-rca"           # Standard RCA
    - "auto-fix"            # Auto-fix with PR
    - "critical-defect"     # High-priority defects
```

### Rate Limiting

Control how many tickets are processed per run:

```yaml
scheduler:
  max_tickets_per_run: 5  # Process max 5 tickets at a time
```

---

## 📊 Monitoring

### Check Scheduler Logs

```bash
# View live logs
tail -f logs/rca_scheduler.log

# Search for PR creation events
grep "GitHub PR created" logs/rca_scheduler.log
```

### Check Analysis Reports

All reports are saved to:
```
output/
  tickets/
    KAN-16/
      KAN-16_rca.html     # HTML report
      KAN-16_rca.md       # Markdown report
      attachments/        # DLT logs
      dlt_logs/           # Processed logs
```

---

## 🎉 Success Metrics

With automatic PR creation enabled, expect:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Time to PR | 2-3 days | 15-30 min | **95%** faster |
| Manual effort | 4-6 hours | < 30 min | **90%** reduction |
| Developer context | Low | High | RCA included in PR |

---

## 📞 Support

If you encounter issues:

1. Check logs: `logs/rca_scheduler.log`
2. Verify configuration: `config/config.yaml`
3. Test Git connection: `python demo_create_pr.py`
4. Test JIRA connection: `python jira_data_fetcher.py`

For detailed documentation, see:
- [README.md](README.md) - Full system documentation
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Initial setup instructions
