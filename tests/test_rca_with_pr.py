#!/usr/bin/env python
"""
Test RCA Engine with Dashboard AND GitHub PR Creation

This test demonstrates the COMPLETE workflow:
1. Starts real-time dashboard for monitoring
2. Runs RCA analysis on a defect
3. Generates code fix based on RCA
4. Creates a GitHub Pull Request with the fix
5. Shows all updates live in the dashboard

Usage:
    python test_rca_with_pr.py
    python test_rca_with_pr.py --defect-id TEST-DASHBOARD-001
"""

import os
import sys
import time
import argparse
import webbrowser

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.llm_service import LLMService
from src.rca_infotainment.git_service import GitService
from src.rca_infotainment.dashboard.dashboard_server import RCADashboard
from src.utils.config import load_config

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    """Run RCA analysis with GitHub PR creation"""
    
    parser = argparse.ArgumentParser(description='RCA Test with PR Creation')
    parser.add_argument('--defect-id', default='TEST-DASHBOARD-001',
                       help='Defect ID to analyze (default: TEST-DASHBOARD-001)')
    parser.add_argument('--no-pr', action='store_true',
                       help='Skip PR creation (analysis only)')
    parser.add_argument('--no-dashboard', action='store_true',
                       help='Skip dashboard (headless mode)')
    parser.add_argument('--from-jira', action='store_true',
                       help='Fetch defect from JIRA instead of local files')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  RCA ENGINE TEST WITH GITHUB PR CREATION")
    print("="*70)
    print()
    
    # Load configuration
    config = load_config('config/config.yaml')
    
    # Start dashboard (unless disabled)
    dashboard = None
    if not args.no_dashboard:
        print("Starting dashboard server...")
        dashboard = RCADashboard(port=5050)
        dashboard.start(open_browser=True)
        print(f"✓ Dashboard running at http://localhost:5050")
        print()
        time.sleep(2)  # Let dashboard start
    
    # Initialize RCA Engine
    print("Initializing RCA Engine...")
    rca_engine = RCAEngine(config=config)
    
    # Connect dashboard
    if dashboard:
        rca_engine.set_dashboard(dashboard)
        print("✓ Dashboard connected to RCA engine")
    
    # Initialize LLM service
    print("Initializing LLM service...")
    llm_service = LLMService(config=config)
    if llm_service.is_available():
        rca_engine.set_llm_client(llm_service)
        print("✓ LLM service connected")
    else:
        print("⚠ LLM service not available - using mock analysis")
    
    # Initialize JIRA client (if fetching from JIRA)
    jira_client = None
    if args.from_jira:
        print("Initializing JIRA client...")
        try:
            from jira_data_fetcher import JiraDataFetcher
            jira_config = config.get('integrations', {}).get('jira', {})
            jira_url = jira_config.get('url') or os.getenv('JIRA_URL') or os.getenv('JIRA_BASE_URL')
            jira_email = jira_config.get('email') or os.getenv('JIRA_EMAIL')
            jira_token = jira_config.get('api_token') or os.getenv('JIRA_API_TOKEN')
            
            if jira_url and jira_email and jira_token:
                jira_client = JiraDataFetcher(jira_url, jira_email, jira_token)
                if jira_client.test_connection():
                    rca_engine.set_jira_client(jira_client)
                    print(f"✓ JIRA connected: {jira_url}")
                else:
                    print("✗ JIRA connection failed")
            else:
                print("✗ JIRA credentials not found in .env")
                print("  Cannot fetch from JIRA without credentials!")
                return
        except Exception as e:
            print(f"✗ Failed to initialize JIRA: {e}")
            return
    
    # Initialize Git service
    print("Initializing Git service...")
    git_config = config.get('integrations', {}).get('git', {})
    git_service = GitService(git_config)
    
    if git_service.is_connected():
        rca_engine.set_git_client(git_service)
        print(f"✓ Git connected: {git_service.repo_url}")
        
        # Check if we can create PRs
        if 'github.com' in git_service.repo_url:
            print("✓ GitHub repository detected - PR creation enabled")
        else:
            print("ℹ Non-GitHub repository - PR creation may not work")
    else:
        print("✗ Git not connected - PR creation will fail!")
        print("  Check GIT_REPO_URL, GIT_TOKEN in .env")
        if not args.no_pr:
            print("\nCannot proceed without Git. Exiting...")
            return
    
    print()
    print("-"*70)
    print("STARTING RCA ANALYSIS & FIX WORKFLOW")
    print(f"Defect ID: {args.defect_id}")
    print(f"Create PR: {not args.no_pr}")
    print(f"From JIRA: {args.from_jira}")
    print("-"*70)
    print()
    
    defect_id = args.defect_id
    
    try:
        if args.no_pr:
            # Analysis only (no PR)
            print("Mode: ANALYSIS ONLY (No PR creation)")
            print()
            
            result = rca_engine.analyze_defect(
                defect_id=defect_id,
                from_jira=args.from_jira,
                upload_to_jira=False,
                mark_duplicates=False
            )
            
            print()
            print("="*70)
            print("RCA ANALYSIS COMPLETE")
            print("="*70)
            print()
            
            if result.get('status') == 'completed':
                print(f"✓ Status: SUCCESS")
                print(f"  Root Cause: {result.get('root_cause', 'N/A')[:150]}...")
                print(f"  Confidence: {result.get('confidence', 0):.0%}")
                print(f"  Domain: {result.get('domain', 'Unknown')}")
                print(f"  Duration: {result.get('duration_seconds', 0):.1f}s")
            else:
                print(f"✗ Status: FAILED")
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        else:
            # Complete workflow: Analysis + Fix + PR
            print("Mode: COMPLETE WORKFLOW (Analysis + Fix + PR Creation)")
            print()
            
            result = rca_engine.analyze_and_fix(
                defect_id=defect_id,
                from_jira=args.from_jira,
                upload_to_jira=False,
                create_pr=True
            )
            
            print()
            print("="*70)
            print("RCA ANALYSIS & FIX WORKFLOW COMPLETE")
            print("="*70)
            print()
            
            # Show analysis results
            analysis = result.get('analysis', {})
            if analysis.get('status') == 'completed':
                print("✓ ANALYSIS: SUCCESS")
                print(f"  Root Cause: {analysis.get('root_cause', 'N/A')[:150]}...")
                print(f"  Confidence: {analysis.get('confidence', 0):.0%}")
                print(f"  Duration: {analysis.get('duration_seconds', 0):.1f}s")
                print()
            else:
                print("✗ ANALYSIS: FAILED")
                print(f"  Error: {analysis.get('error', 'Unknown')}")
                print()
            
            # Show PR results
            pr_result = result.get('pr_result')
            if pr_result:  # Check if pr_result exists (not None)
                if pr_result.get('success'):
                    print("✓ PULL REQUEST: CREATED")
                    pr_info = pr_result.get('pr', {})
                    print(f"  Branch: {pr_result.get('branch', 'N/A')}")
                    print(f"  PR Number: #{pr_info.get('number', 'N/A')}")
                    print(f"  PR Title: {pr_info.get('title', 'N/A')}")
                    print(f"  PR URL: {pr_info.get('url', 'N/A')}")
                    print()
                    
                    # Open PR in browser
                    if pr_info.get('url'):
                        print("Opening PR in browser...")
                        webbrowser.open(pr_info['url'])
                    
                elif pr_result.get('partial_success'):
                    print("⚠ PULL REQUEST: PARTIAL SUCCESS")
                    print(f"  Branch created: {pr_result.get('branch', 'N/A')}")
                    print(f"  Fixes applied: {len(pr_result.get('fixes_applied', []))}")
                    print(f"  Errors: {', '.join(pr_result.get('errors', []))}")
                    print()
                else:
                    print("✗ PULL REQUEST: FAILED")
                    print(f"  Errors:")
                    for error in pr_result.get('errors', []):
                        print(f"    - {error}")
                    print()
            else:
                print("⚠ PULL REQUEST: SKIPPED")
                print("  Analysis failed, PR creation was not attempted")
                print()
            
            # Token metrics
            token_metrics = analysis.get('token_metrics', {})
            if token_metrics:
                print("Token Usage:")
                print(f"  Input: {token_metrics.get('total_input', 0):,}")
                print(f"  Output: {token_metrics.get('total_output', 0):,}")
                print(f"  Total: {token_metrics.get('total_tokens', 0):,}")
                print(f"  Cost: €{token_metrics.get('estimated_cost_eur', 0):.4f}")
                print()
            
            # Reports
            reports = analysis.get('reports', {})
            if reports:
                print("Reports generated:")
                md_report = reports.get('markdown_report', '')
                html_report = reports.get('html_report', '')
                
                if md_report and os.path.exists(md_report):
                    print(f"  📄 Markdown: {md_report}")
                if html_report and os.path.exists(html_report):
                    print(f"  🌐 HTML: {html_report}")
                print()
    
    except Exception as e:
        print(f"\n✗ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
    
    # Keep dashboard running
    if dashboard:
        print("-"*70)
        print("Dashboard is still running for review")
        print("Press Ctrl+C to stop")
        print("-"*70)
        print()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            dashboard.stop()
            print("Goodbye!")


if __name__ == "__main__":
    main()
