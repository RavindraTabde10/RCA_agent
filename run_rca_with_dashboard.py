#!/usr/bin/env python
"""
RCA Scheduler with Live Dashboard

This script:
1. Starts the real-time monitoring dashboard on port 5050
2. Runs the RCA scheduler to process JIRA tickets
3. Displays live analysis progress in the dashboard

Usage:
    python run_rca_with_dashboard.py                # Run once
    python run_rca_with_dashboard.py --daemon       # Continuous monitoring
    python run_rca_with_dashboard.py --interval 300 # Check every 5 minutes
    python run_rca_with_dashboard.py --dry-run      # Test mode (no JIRA updates)
"""

import os
import sys
import time
import json
import logging
import argparse
import threading
import webbrowser
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
from jira_data_fetcher import JiraDataFetcher

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=open(1, 'w', encoding='utf-8', closefd=False)),
        logging.FileHandler('logs/rca_with_dashboard.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class RCASchedulerWithDashboard:
    """RCA Scheduler with integrated live dashboard"""
    
    DEFAULT_CONFIG = {
        'trigger_labels': ['needs-rca', 'auto-rca', 'rca-requested'],
        'completion_label': 'rca-complete',
        'in_progress_label': 'rca-in-progress',
        'error_label': 'rca-error',
        'max_tickets_per_run': 10,
        'jql_filter': 'status != Closed AND status != Done',
        'remove_trigger_label': True,
        'upload_to_jira': True,
        'mark_duplicates': True,
    }
    
    def __init__(self, config_path: str = "config/config.yaml", dry_run: bool = False, 
                 dashboard_port: int = 5050):
        """
        Initialize RCA Scheduler with Dashboard
        
        Args:
            config_path: Path to configuration file
            dry_run: If True, don't update JIRA (test mode)
            dashboard_port: Port for dashboard server
        """
        self.dry_run = dry_run
        self.config = load_config(config_path)
        self.scheduler_config = {**self.DEFAULT_CONFIG, **self.config.get('scheduler', {})}
        
        # Initialize dashboard
        self.dashboard = RCADashboard(port=dashboard_port)
        
        # Initialize components
        self.rca_engine = None
        self.jira_fetcher = None
        self.llm_service = None
        
        # Statistics
        self.stats = {
            'total_runs': 0,
            'total_processed': 0,
            'total_success': 0,
            'total_failed': 0
        }
    
    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing RCA Scheduler with Dashboard...")
        
        # Start dashboard in background
        self.dashboard.start(open_browser=True)
        logger.info(f"✓ Dashboard started at http://localhost:{self.dashboard.port}")
        
        # Initialize JIRA
        jira_url = os.getenv("JIRA_BASE_URL") or os.getenv("JIRA_URL")
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_API_TOKEN")
        
        if jira_url and jira_email and jira_token:
            self.jira_fetcher = JiraDataFetcher(jira_url, jira_email, jira_token)
            if self.jira_fetcher.test_connection():
                logger.info("✓ JIRA connected")
            else:
                logger.error("✗ JIRA connection failed")
                return False
        else:
            logger.warning("⚠ JIRA credentials not found")
            return False
        
        # Initialize RCA Engine
        self.rca_engine = RCAEngine(config=self.config)
        
        # Connect dashboard to RCA engine for live monitoring
        self.rca_engine.set_dashboard(self.dashboard)
        logger.info("✓ Dashboard connected to RCA engine")
        
        # Initialize LLM
        self.llm_service = LLMService(config=self.config)
        if self.llm_service.is_available():
            self.rca_engine.set_llm_client(self.llm_service)
            logger.info("✓ LLM service initialized")
        else:
            logger.warning("✗ LLM service not available - using mock analysis")
        
        # Configure JIRA client on RCA engine
        if self.jira_fetcher:
            self.rca_engine.set_jira_client(self.jira_fetcher)
            logger.info("✓ JIRA client set on RCA engine")
        
        # Git service (optional)
        try:
            self.git_service = GitService(config=self.config)
            self.rca_engine.git_service = self.git_service
        except Exception as e:
            logger.warning(f"Git service not available: {e}")
        
        logger.info("✓ RCA Engine initialized")
        logger.info(f"RCA Scheduler initialized (dry_run={self.dry_run})")
        logger.info(f"Trigger labels: {self.scheduler_config['trigger_labels']}")
        
        return True
    
    def process_ticket(self, ticket: Dict[str, Any]) -> bool:
        """
        Process a single JIRA ticket with dashboard tracking
        
        Args:
            ticket: JIRA ticket data
            
        Returns:
            True if successful, False otherwise
        """
        issue_key = ticket.get('key')
        
        logger.info("")
        logger.info("="*60)
        logger.info(f"Processing ticket: {issue_key}")
        logger.info(f"Summary: {ticket.get('summary', 'N/A')}")
        logger.info("="*60)
        
        try:
            # Create workspace
            workspace = self._create_ticket_workspace(issue_key)
            logger.info(f"   Workspace: {workspace}")
            
            # Download attachments (before RCA starts)
            logger.info(f"   📥 Attempting to download attachments...")
            downloaded = self._download_attachments(ticket, workspace)
            logger.info(f"   ✅ Downloaded {len(downloaded)} attachment(s)")
            for f in downloaded:
                logger.info(f"      - {os.path.basename(f)}")
            
            # Update JIRA labels (in-progress)
            if not self.dry_run:
                self._update_jira_label(issue_key, self.scheduler_config['in_progress_label'], add=True)
            
            # Run RCA analysis (RCA engine handles all dashboard updates)
            logger.info(f"   🔍 Starting RCA analysis...")
            
            # Note: RCA engine will fetch from JIRA when from_jira=True
            # Attachments are already downloaded to workspace
            result = self.rca_engine.analyze_defect(
                defect_id=issue_key,
                from_jira=True,
                upload_to_jira=not self.dry_run,
                mark_duplicates=self.scheduler_config.get('mark_duplicates', True)
            )
            
            # Check if RCA completed successfully (status == "completed")
            if result.get('status') == 'completed':
                logger.info(f"   ✅ RCA completed successfully")
                confidence = result.get('confidence', 0)
                domain = result.get('domain', 'Unknown')
                
                # Upload report if requested
                if not self.dry_run and self.scheduler_config.get('upload_to_jira'):
                    self._upload_report_to_jira(issue_key, result)
                
                # Update labels (completion)
                if not self.dry_run:
                    self._finalize_jira_labels(issue_key, success=True)
                
                self.stats['total_success'] += 1
                return True
            else:
                # RCA engine already completed dashboard tracking
                logger.error(f"   ✗ RCA failed: {result.get('error', 'Unknown error')}")
                
                if not self.dry_run:
                    self._finalize_jira_labels(issue_key, success=False)
                
                self.stats['total_failed'] += 1
                return False
                
        except Exception as e:
            # Error occurred before RCA started (e.g., workspace creation, download)
            logger.error(f"   ✗ Error processing {issue_key}: {e}", exc_info=True)
            
            # Notify dashboard of failure
            if self.dashboard:
                self.dashboard.complete_analysis(issue_key, success=False)
            
            if not self.dry_run:
                self._finalize_jira_labels(issue_key, success=False)
            
            self.stats['total_failed'] += 1
            return False
    
    def _create_ticket_workspace(self, issue_key: str) -> str:
        """Create workspace folder for ticket"""
        ticket_folder = os.path.join(".", "output", "tickets", issue_key)
        os.makedirs(ticket_folder, exist_ok=True)
        logger.info(f"📁 Created workspace for {issue_key}: {ticket_folder}")
        return ticket_folder
    
    def _download_attachments(self, ticket: Dict[str, Any], workspace: str) -> List[str]:
        """Download attachments from ticket"""
        downloaded = []
        issue_key = ticket.get('key')
        
        if self.jira_fetcher:
            try:
                files = self.jira_fetcher.download_dlt_attachments(issue_key, workspace)
                downloaded.extend(files)
            except Exception as e:
                logger.warning(f"Failed to download attachments: {e}")
        
        return downloaded
    
    def _update_jira_label(self, issue_key: str, label: str, add: bool = True):
        """Add or remove label from JIRA ticket"""
        if self.dry_run:
            action = "add" if add else "remove"
            logger.info(f"  [DRY RUN] Would {action} label '{label}' on {issue_key}")
            return
        
        try:
            if add:
                self.jira_fetcher.add_label(issue_key, label)
                logger.info(f"  ✓ Added label '{label}' on {issue_key}")
            else:
                self.jira_fetcher.remove_label(issue_key, label)
                logger.info(f"  ✓ Removed label '{label}' from {issue_key}")
        except Exception as e:
            logger.warning(f"Failed to update label: {e}")
    
    def _finalize_jira_labels(self, issue_key: str, success: bool):
        """Update JIRA labels after analysis"""
        # Remove in-progress label
        self._update_jira_label(issue_key, self.scheduler_config['in_progress_label'], add=False)
        
        # Remove trigger labels if configured
        if self.scheduler_config.get('remove_trigger_label'):
            for label in self.scheduler_config['trigger_labels']:
                self._update_jira_label(issue_key, label, add=False)
        
        # Add completion/error label
        if success:
            self._update_jira_label(issue_key, self.scheduler_config['completion_label'], add=True)
        else:
            self._update_jira_label(issue_key, self.scheduler_config['error_label'], add=True)
    
    def _upload_report_to_jira(self, issue_key: str, result: Dict[str, Any]):
        """Upload RCA report to JIRA"""
        # TODO: Implement report upload
        logger.info(f"  📤 Would upload report for {issue_key}")
    
    def run_once(self):
        """Run scheduler once"""
        self.stats['total_runs'] += 1
        
        logger.info("")
        logger.info("="*80)
        logger.info(f"RCA SCHEDULER RUN #{self.stats['total_runs']}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("="*80)
        
        # Search for tickets
        logger.info(f"Searching for tickets with labels: {self.scheduler_config['trigger_labels']}")
        
        tickets = self.jira_fetcher.fetch_by_labels(
            labels=self.scheduler_config['trigger_labels'],
            project_key=os.getenv("JIRA_PROJECT_KEY"),
            additional_filter=self.scheduler_config.get('jql_filter'),
            max_results=self.scheduler_config.get('max_tickets_per_run', 10)
        )
        
        logger.info(f"Found {len(tickets)} tickets to analyze")
        
        if not tickets:
            logger.info("No tickets found with trigger labels")
            return
        
        # Process each ticket
        for ticket in tickets:
            self.stats['total_processed'] += 1
            self.process_ticket(ticket)
    
    def run_daemon(self, interval: int = 300):
        """Run scheduler continuously"""
        logger.info(f"Starting daemon mode (interval: {interval}s)")
        
        try:
            while True:
                self.run_once()
                logger.info(f"\nWaiting {interval}s until next run...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\nShutting down daemon...")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown scheduler and dashboard"""
        logger.info("\n" + "="*60)
        logger.info("FINAL STATISTICS")
        logger.info("="*60)
        logger.info(f"Total runs: {self.stats['total_runs']}")
        logger.info(f"Total tickets processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['total_success']}")
        logger.info(f"Failed: {self.stats['total_failed']}")
        
        # Stop dashboard
        self.dashboard.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='RCA Scheduler with Live Dashboard')
    parser.add_argument('--daemon', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=300, help='Interval between runs (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Test mode (no JIRA updates)')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--port', type=int, default=5050, help='Dashboard port')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  RCA SCHEDULER WITH LIVE DASHBOARD")
    print("  Automated Root Cause Analysis for JIRA Tickets")
    print("="*60)
    
    # Create and initialize scheduler
    scheduler = RCASchedulerWithDashboard(
        config_path=args.config,
        dry_run=args.dry_run,
        dashboard_port=args.port
    )
    
    if not scheduler.initialize():
        print("\n✗ Initialization failed. Check logs.")
        sys.exit(1)
    
    # Run scheduler
    try:
        if args.daemon:
            scheduler.run_daemon(interval=args.interval)
        else:
            scheduler.run_once()
            
            # Keep dashboard running
            print("\n" + "-"*60)
            print("  Analysis complete. Dashboard still running.")
            print("  Press Ctrl+C to stop.")
            print("-"*60 + "\n")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
