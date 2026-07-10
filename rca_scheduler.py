#!/usr/bin/env python
"""
RCA Scheduler - Automated Root Cause Analysis Job

This script runs as a scheduled job to:
1. Fetch JIRA tickets with specific labels (e.g., 'needs-rca')
2. Run RCA analysis on each ticket
3. Update JIRA with results (comment, reports, duplicate links)
4. Update labels (remove trigger label, add completion label)

NO MANUAL INTERVENTION REQUIRED - Fully automated!

Schedule this script using:
- Windows Task Scheduler
- Linux cron
- Azure Functions Timer Trigger
- AWS Lambda + CloudWatch Events

Usage:
    python rca_scheduler.py                    # Run once
    python rca_scheduler.py --daemon           # Run continuously
    python rca_scheduler.py --interval 300    # Run every 5 minutes
    python rca_scheduler.py --dry-run          # Test without JIRA updates
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.llm_service import LLMService
from src.rca_infotainment.git_service import GitService
from src.rca_infotainment.dashboard.dashboard_server import RCADashboard
from src.utils.config import load_config

# Import the simple JIRA fetcher (uses standard library only)
from jira_data_fetcher import JiraDataFetcher

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=open(1, 'w', encoding='utf-8', closefd=False)),
        logging.FileHandler('logs/rca_scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class RCAScheduler:
    """
    Automated RCA Scheduler
    
    Monitors JIRA for tickets with specific labels and runs RCA automatically.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'trigger_labels': ['needs-rca', 'auto-rca', 'rca-requested'],  # Labels that trigger RCA
        'completion_label': 'rca-complete',                             # Label added after RCA
        'in_progress_label': 'rca-in-progress',                         # Label while analyzing
        'error_label': 'rca-error',                                     # Label on error
        'max_tickets_per_run': 10,                                      # Max tickets to process per run
        'jql_filter': 'status != Closed',                               # Additional JQL filter
        'remove_trigger_label': True,                                   # Remove trigger label after RCA
        'upload_to_jira': True,                                         # Upload reports to JIRA
        'mark_duplicates': True,                                        # Link duplicate tickets
        'auto_create_pr': True,                                         # Automatically create GitHub PR with fix
    }
    
    def __init__(self, config_path: str = "config/config.yaml", dry_run: bool = False, enable_dashboard: bool = False, dashboard_port: int = 5050):
        """
        Initialize RCA Scheduler
        
        Args:
            config_path: Path to configuration file
            dry_run: If True, don't update JIRA (test mode)
            enable_dashboard: If True, start live monitoring dashboard
            dashboard_port: Port for dashboard server (default: 5050)
        """
        self.dry_run = dry_run
        self.enable_dashboard = enable_dashboard
        self.dashboard_port = dashboard_port
        self.config = load_config(config_path)
        self.scheduler_config = {**self.DEFAULT_CONFIG, **self.config.get('scheduler', {})}
        
        # Initialize services
        self.jira_fetcher = None
        self.rca_engine = None
        self.dashboard = None
        self._init_services()
        
        # Statistics
        self.stats = {
            'runs': 0,
            'tickets_processed': 0,
            'tickets_success': 0,
            'tickets_failed': 0,
            'duplicates_found': 0,
            'last_run': None
        }
        
        logger.info(f"RCA Scheduler initialized (dry_run={dry_run})")
        logger.info(f"Trigger labels: {self.scheduler_config['trigger_labels']}")
        logger.info(f"Auto-create PR: {self.scheduler_config.get('auto_create_pr', False)}")
    
    def _init_services(self):
        """Initialize all required services"""
        # Initialize Dashboard (if enabled)
        if self.enable_dashboard:
            try:
                logger.info(f"Starting dashboard on port {self.dashboard_port}...")
                self.dashboard = RCADashboard(port=self.dashboard_port)
                self.dashboard.start(open_browser=False)  # Don't auto-open browser in scheduler mode
                logger.info(f"✓ Dashboard started at http://localhost:{self.dashboard_port}")
            except Exception as e:
                logger.warning(f"✗ Failed to start dashboard: {e}")
                self.dashboard = None
        
        # Initialize JIRA Data Fetcher (uses standard library - no requests needed)
        try:
            jira_config = self.config.get('integrations', {}).get('jira', {})
            jira_url = jira_config.get('url') or os.getenv('JIRA_URL') or os.getenv('JIRA_BASE_URL')
            jira_email = jira_config.get('email') or os.getenv('JIRA_EMAIL')
            jira_token = jira_config.get('api_token') or os.getenv('JIRA_API_TOKEN')
            self.project_key = jira_config.get('project_key') or os.getenv('JIRA_PROJECT_KEY')
            
            if jira_url and jira_email and jira_token:
                self.jira_fetcher = JiraDataFetcher(jira_url, jira_email, jira_token)
                
                if self.jira_fetcher.test_connection():
                    logger.info("✓ JIRA connected")
                else:
                    logger.warning("✗ JIRA connection failed - check credentials")
                    self.jira_fetcher = None
            else:
                logger.warning("✗ JIRA not configured - set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN")
                self.jira_fetcher = None
                
        except Exception as e:
            logger.error(f"Failed to initialize JIRA: {e}")
            self.jira_fetcher = None
        
        # Initialize RCA Engine
        try:
            self.rca_engine = RCAEngine(self.config)
            
            # Set LLM client
            llm_service = LLMService(self.config)
            if llm_service.is_available():
                self.rca_engine.set_llm_client(llm_service)
                logger.info("✓ LLM service connected")
            else:
                logger.warning("✗ LLM service not available - using mock analysis")
            
            # Set JIRA client (required for from_jira=True)
            if self.jira_fetcher:
                self.rca_engine.set_jira_client(self.jira_fetcher)
                logger.info("✓ JIRA client set on RCA engine")
            
            # Connect dashboard to RCA engine for live monitoring
            if self.dashboard:
                self.rca_engine.set_dashboard(self.dashboard)
                logger.info("✓ Dashboard connected to RCA engine")
            
            # Set Git client (optional)
            try:
                git_config = self.config.get('integrations', {}).get('git', {})
                git_service = GitService(git_config)
                if git_service.is_connected():
                    self.rca_engine.set_git_client(git_service)
                    logger.info("✓ Git service connected")
            except Exception as e:
                logger.info(f"Git service not available: {e}")
            
            logger.info("✓ RCA Engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RCA Engine: {e}")
            raise
        
        # Base directory for ticket workspaces (use base_path, not output_dir)
        base_path = self.config.get('paths', {}).get('base_path', '.')
        self.tickets_workspace = os.path.join(base_path, 'output', 'tickets')
        os.makedirs(self.tickets_workspace, exist_ok=True)
    
    def _create_ticket_workspace(self, issue_key: str) -> str:
        """
        Create isolated workspace folder for a ticket
        
        Simple structure:
        - output/tickets/TICKET-123/  (all files directly inside)
        
        Args:
            issue_key: JIRA ticket key (e.g., 'PROJ-123')
            
        Returns:
            Path to ticket workspace folder
        """
        # Sanitize issue key for folder name
        safe_key = issue_key.replace('/', '_').replace('\\', '_')
        ticket_folder = os.path.join(self.tickets_workspace, safe_key)
        
        # Create ticket folder
        os.makedirs(ticket_folder, exist_ok=True)
        
        logger.info(f"📁 Created workspace for {issue_key}: {ticket_folder}")
        return ticket_folder
    
    def _download_ticket_attachments(self, ticket: Dict[str, Any], workspace: str) -> List[str]:
        """
        Download DLT and log attachments from JIRA ticket to workspace
        
        Args:
            ticket: JIRA ticket data
            workspace: Ticket workspace folder
            
        Returns:
            List of downloaded file paths
        """
        downloaded = []
        attachments_dir = os.path.join(workspace, 'attachments')
        dlt_dir = os.path.join(workspace, 'dlt_logs')
        
        # Get attachments from ticket
        attachments = ticket.get('attachments', [])
        if not attachments:
            # Try to get from fields
            fields = ticket.get('fields', {})
            attachments = fields.get('attachment', [])
        
        for attachment in attachments:
            filename = attachment.get('filename', '')
            # Try different key names for download URL (varies by JIRA API version)
            download_url = (attachment.get('content_url') or 
                           attachment.get('content') or 
                           attachment.get('url', ''))
            
            if not filename or not download_url:
                continue
            
            # Check if it's a DLT or log file
            is_dlt = filename.lower().endswith(('.dlt', '.log', '.txt'))
            target_dir = dlt_dir if is_dlt else attachments_dir
            target_path = os.path.join(target_dir, filename)
            
            try:
                if self.jira_fetcher:
                    # Download using JIRA fetcher (handles auth)
                    success = self.jira_fetcher.download_attachment(download_url, target_path)
                    if success:
                        downloaded.append(target_path)
                        logger.info(f"   📥 Downloaded: {filename}")
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to download {filename}: {e}")
        
        return downloaded
    
    def _configure_engine_for_ticket(self, workspace: str):
        """
        Configure RCA engine to use ticket-specific directories
        
        Args:
            workspace: Ticket workspace folder
        """
        # Update engine paths to use ticket workspace (all files in same folder)
        self.rca_engine.dlt_logs_dir = workspace
        self.rca_engine.output_dir = workspace
    
    def fetch_tickets_by_label(self, labels: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch JIRA tickets with specified labels
        
        Args:
            labels: List of labels to search for
            
        Returns:
            List of matching tickets
        """
        if not self.jira_fetcher:
            logger.error("JIRA not connected - cannot fetch tickets")
            return []
        
        labels = labels or self.scheduler_config['trigger_labels']
        additional_filter = self.scheduler_config.get('jql_filter', 'status != Closed')
        
        logger.info(f"Searching for tickets with labels: {labels}")
        
        try:
            tickets = self.jira_fetcher.fetch_by_labels(
                labels=labels,
                project_key=self.project_key,
                additional_filter=additional_filter,
                max_results=self.scheduler_config['max_tickets_per_run']
            )
            logger.info(f"Found {len(tickets)} tickets to analyze")
            return tickets
        except Exception as e:
            logger.error(f"Failed to fetch tickets: {e}")
            return []
    
    def update_ticket_label(self, issue_key: str, add_labels: List[str] = None, 
                           remove_labels: List[str] = None) -> bool:
        """
        Update labels on a JIRA ticket
        
        Args:
            issue_key: JIRA issue key
            add_labels: Labels to add
            remove_labels: Labels to remove
            
        Returns:
            Success status
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update labels on {issue_key}: "
                       f"add={add_labels}, remove={remove_labels}")
            return True
        
        if not self.jira_fetcher:
            return False
        
        try:
            return self.jira_fetcher.update_labels(issue_key, add_labels, remove_labels)
        except Exception as e:
            logger.error(f"Failed to update labels on {issue_key}: {e}")
            return False
    
    def add_rca_comment(self, issue_key: str, rca_result: Dict[str, Any]) -> bool:
        """
        Add RCA result as comment to JIRA ticket
        
        Args:
            issue_key: JIRA issue key
            rca_result: RCA analysis result
            
        Returns:
            Success status
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would add RCA comment to {issue_key}")
            return True
        
        if not self.jira_fetcher:
            return False
        
        # Format RCA result as comment
        comment = self._format_rca_comment(rca_result)
        
        try:
            return self.jira_fetcher.add_comment(issue_key, comment)
        except Exception as e:
            logger.error(f"Failed to add comment to {issue_key}: {e}")
            return False
    
    def _format_rca_comment(self, rca_result: Dict[str, Any]) -> str:
        """Format RCA result as JIRA comment"""
        lines = []
        lines.append("🔍 ROOT CAUSE ANALYSIS REPORT")
        lines.append("=" * 40)
        lines.append("")
        
        # Root cause
        root_cause = rca_result.get('root_cause', 'Unable to determine')
        lines.append(f"📌 ROOT CAUSE:")
        lines.append(root_cause[:500] if len(root_cause) > 500 else root_cause)
        lines.append("")
        
        # Confidence
        confidence = rca_result.get('confidence', 0)
        lines.append(f"📊 CONFIDENCE: {confidence:.0%}")
        lines.append("")
        
        # Duplicate info
        duplicate_info = rca_result.get('duplicate_info', {})
        if duplicate_info.get('is_duplicate'):
            lines.append(f"⚠️ POTENTIAL DUPLICATE OF: {duplicate_info.get('duplicate_of')}")
            lines.append(f"   Similarity: {duplicate_info.get('similarity', 0):.0%}")
            lines.append("")
        
        # Fix recommendation
        fix = rca_result.get('fix_recommendation', '')
        if fix:
            lines.append("💡 FIX RECOMMENDATION:")
            lines.append(fix[:500] if len(fix) > 500 else fix)
            lines.append("")
        
        lines.append("-" * 40)
        lines.append(f"Generated by RCA Agent at {datetime.now().isoformat()}")
        
        return "\n".join(lines)
    
    def process_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single ticket through RCA
        
        Each ticket gets its own isolated workspace folder to prevent
        DLT file contamination between analyses.
        
        Args:
            ticket: JIRA ticket data
            
        Returns:
            RCA result
        """
        issue_key = ticket.get('key')
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing ticket: {issue_key}")
        logger.info(f"Summary: {ticket.get('summary', 'N/A')}")
        logger.info(f"{'='*60}")
        
        result = {
            'issue_key': issue_key,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        # Store original paths to restore later
        original_dlt_dir = self.rca_engine.dlt_logs_dir
        original_output_dir = self.rca_engine.output_dir
        
        try:
            # ========================================
            # STEP 1: Create isolated ticket workspace
            # ========================================
            workspace = self._create_ticket_workspace(issue_key)
            result['workspace'] = workspace
            
            # Configure RCA engine to use ticket-specific paths
            self._configure_engine_for_ticket(workspace)
            logger.info(f"   Workspace: {workspace}")
            
            # ========================================
            # STEP 2: Download attachments
            # ========================================
            # Use optimized method - no extra API call since we have ticket data
            logger.info(f"   📥 Attempting to download attachments...")
            downloaded_files = self.jira_fetcher.download_ticket_attachments_to_workspace(ticket, workspace)
            if downloaded_files:
                logger.info(f"   ✅ Downloaded {len(downloaded_files)} attachment(s)")
                for f in downloaded_files:
                    logger.info(f"      - {os.path.basename(f)}")
            else:
                logger.warning(f"   ⚠️ No attachments downloaded")
            
            # ========================================
            # STEP 3: Add in-progress label
            # ========================================
            in_progress_label = self.scheduler_config.get('in_progress_label')
            if in_progress_label:
                self.update_ticket_label(
                    issue_key,
                    add_labels=[in_progress_label]
                )
            
            # ========================================
            # STEP 4: Run RCA analysis (with optional PR creation)
            # ========================================
            auto_create_pr = self.scheduler_config.get('auto_create_pr', False)
            
            if auto_create_pr:
                # Use analyze_and_fix for complete workflow (analysis + PR)
                logger.info(f"   Running analysis with automatic PR creation...")
                workflow_result = self.rca_engine.analyze_and_fix(
                    defect_id=issue_key,
                    from_jira=True,  # Fetch fresh data from JIRA
                    upload_to_jira=self.scheduler_config['upload_to_jira'] and not self.dry_run,
                    create_pr=True
                )
                
                # Extract analysis result
                rca_result = workflow_result.get('analysis', {})
                result['rca_result'] = rca_result
                result['root_cause'] = rca_result.get('root_cause', 'Unknown')
                result['confidence'] = rca_result.get('confidence', 0)
                
                # Store PR result
                pr_result = workflow_result.get('pr_result')
                if pr_result:
                    result['pr_result'] = pr_result
                    if pr_result.get('success'):
                        pr_info = pr_result.get('pr', {})
                        result['pr_number'] = pr_info.get('number')
                        result['pr_url'] = pr_info.get('url')
                        logger.info(f"   ✓ GitHub PR created: {result['pr_url']}")
                    else:
                        logger.warning(f"   PR creation check: {pr_result.get('errors', [])}")
            else:
                # Standard analysis only (no PR creation)
                logger.info(f"   Running standard RCA analysis...")
                rca_result = self.rca_engine.analyze_defect(
                    defect_id=issue_key,
                    from_jira=True,  # Fetch fresh data from JIRA
                    upload_to_jira=self.scheduler_config['upload_to_jira'] and not self.dry_run,
                    mark_duplicates=self.scheduler_config['mark_duplicates']
                )
                
                result['rca_result'] = rca_result
                result['root_cause'] = rca_result.get('root_cause', 'Unknown')
                result['confidence'] = rca_result.get('confidence', 0)
            
            # Check for duplicates
            duplicate_info = rca_result.get('duplicate_info', {})
            if duplicate_info.get('is_duplicate'):
                result['is_duplicate'] = True
                result['duplicate_of'] = duplicate_info.get('duplicate_of')
                self.stats['duplicates_found'] += 1
                logger.info(f"⚠️ Duplicate detected: {issue_key} → {result['duplicate_of']}")
            
            # ========================================
            # STEP 5: Update labels based on result
            # ========================================
            if rca_result.get('status') == 'completed':
                result['status'] = 'success'
                self.stats['tickets_success'] += 1
                
                completion_label = self.scheduler_config.get('completion_label')
                remove_labels = []
                
                if self.scheduler_config.get('remove_trigger_label'):
                    remove_labels = self.scheduler_config['trigger_labels']
                
                if in_progress_label:
                    remove_labels.append(in_progress_label)
                
                self.update_ticket_label(
                    issue_key,
                    add_labels=[completion_label] if completion_label else None,
                    remove_labels=remove_labels if remove_labels else None
                )
                
                logger.info(f"✅ RCA completed for {issue_key}")
                logger.info(f"   Root Cause: {result['root_cause'][:100]}...")
                logger.info(f"   Confidence: {result['confidence']:.0%}")
                
                # Log PR info if created
                if result.get('pr_url'):
                    logger.info(f"   GitHub PR: {result['pr_url']}")
                    logger.info(f"   PR Number: #{result.get('pr_number', 'N/A')}")
            else:
                result['status'] = 'failed'
                result['error'] = rca_result.get('error', 'Unknown error')
                self.stats['tickets_failed'] += 1
                
                # Add error label
                error_label = self.scheduler_config.get('error_label')
                if error_label:
                    self.update_ticket_label(
                        issue_key,
                        add_labels=[error_label],
                        remove_labels=[in_progress_label] if in_progress_label else None
                    )
                
                logger.error(f"❌ RCA failed for {issue_key}: {result['error']}")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            self.stats['tickets_failed'] += 1
            logger.error(f"❌ Error processing {issue_key}: {e}")
        
        finally:
            # ========================================
            # CLEANUP: Restore original engine paths
            # ========================================
            self.rca_engine.dlt_logs_dir = original_dlt_dir
            self.rca_engine.output_dir = original_output_dir
            logger.info(f"   🔄 Restored engine paths for next ticket")
        
        self.stats['tickets_processed'] += 1
        return result
    
    def run_once(self) -> Dict[str, Any]:
        """
        Run one cycle of the scheduler
        
        Returns:
            Run summary
        """
        self.stats['runs'] += 1
        self.stats['last_run'] = datetime.now().isoformat()
        
        run_summary = {
            'run_number': self.stats['runs'],
            'timestamp': self.stats['last_run'],
            'tickets': [],
            'dry_run': self.dry_run
        }
        
        logger.info("\n" + "="*80)
        logger.info(f"RCA SCHEDULER RUN #{self.stats['runs']}")
        logger.info(f"Timestamp: {self.stats['last_run']}")
        logger.info("="*80)
        
        # Fetch tickets with trigger labels
        tickets = self.fetch_tickets_by_label()
        
        if not tickets:
            logger.info("No tickets found with trigger labels")
            run_summary['tickets_found'] = 0
            return run_summary
        
        run_summary['tickets_found'] = len(tickets)
        
        # Process each ticket
        for ticket in tickets:
            result = self.process_ticket(ticket)
            run_summary['tickets'].append(result)
        
        # Print summary
        logger.info("\n" + "-"*60)
        logger.info("RUN SUMMARY")
        logger.info("-"*60)
        logger.info(f"Tickets processed: {len(run_summary['tickets'])}")
        logger.info(f"Success: {sum(1 for t in run_summary['tickets'] if t['status'] == 'success')}")
        logger.info(f"Failed: {sum(1 for t in run_summary['tickets'] if t['status'] != 'success')}")
        logger.info(f"Duplicates found: {sum(1 for t in run_summary['tickets'] if t.get('is_duplicate'))}")
        
        return run_summary
    
    def run_daemon(self, interval_seconds: int = 300):
        """
        Run continuously as a daemon
        
        Args:
            interval_seconds: Time between runs in seconds
        """
        logger.info(f"Starting RCA Scheduler daemon (interval: {interval_seconds}s)")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Error in scheduler run: {e}")
            
            logger.info(f"\nSleeping for {interval_seconds} seconds...")
            time.sleep(interval_seconds)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return self.stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='RCA Scheduler - Automated Root Cause Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python rca_scheduler.py                     # Run once
    python rca_scheduler.py --dashboard         # Run with live monitoring dashboard
    python rca_scheduler.py --daemon            # Run continuously (5 min interval)
    python rca_scheduler.py --interval 60       # Run every 1 minute
    python rca_scheduler.py --dry-run           # Test mode (no JIRA updates)
    python rca_scheduler.py --dashboard --daemon  # Continuous with dashboard
    python rca_scheduler.py --labels needs-rca auto-analyze

Schedule with Windows Task Scheduler:
    schtasks /create /tn "RCA Scheduler" /tr "python rca_scheduler.py" /sc minute /mo 5

Schedule with cron (Linux):
    */5 * * * * cd /path/to/RCA_agent && python rca_scheduler.py >> logs/cron.log 2>&1
        """
    )
    
    parser.add_argument('--daemon', action='store_true',
                       help='Run continuously as a daemon')
    parser.add_argument('--interval', type=int, default=300,
                       help='Interval between runs in seconds (default: 300)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test mode - do not update JIRA')
    parser.add_argument('--dashboard', action='store_true',
                       help='Enable live monitoring dashboard on port 5050')
    parser.add_argument('--dashboard-port', type=int, default=5050,
                       help='Dashboard port (default: 5050)')
    parser.add_argument('--config', default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--labels', nargs='+',
                       help='Override trigger labels')
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    os.makedirs('logs', exist_ok=True)
    
    print("="*60)
    print("RCA SCHEDULER")
    print("Automated Root Cause Analysis for JIRA Tickets")
    if args.dashboard:
        print(f"Live Dashboard: http://localhost:{args.dashboard_port}")
    print("="*60)
    
    # Initialize scheduler
    scheduler = RCAScheduler(
        config_path=args.config,
        dry_run=args.dry_run,
        enable_dashboard=args.dashboard,
        dashboard_port=args.dashboard_port
    )
    
    # Override labels if provided
    if args.labels:
        scheduler.scheduler_config['trigger_labels'] = args.labels
        logger.info(f"Using custom trigger labels: {args.labels}")
    
    # Run
    if args.daemon:
        scheduler.run_daemon(interval_seconds=args.interval)
    else:
        result = scheduler.run_once()
        
        # Print final stats
        print("\n" + "="*60)
        print("FINAL STATISTICS")
        print("="*60)
        stats = scheduler.get_stats()
        print(f"Total runs: {stats['runs']}")
        print(f"Total tickets processed: {stats['tickets_processed']}")
        print(f"Successful: {stats['tickets_success']}")
        print(f"Failed: {stats['tickets_failed']}")
        print(f"Duplicates found: {stats['duplicates_found']}")


if __name__ == "__main__":
    main()
