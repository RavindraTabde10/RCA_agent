#!/usr/bin/env python
"""
Test RCA Engine with Live Dashboard

This test:
1. Starts the real-time dashboard
2. Uses the actual RCA Engine (not simulation)
3. Shows live token consumption and stage updates
4. Generates HTML reports
5. NO JIRA interaction - uses local test data

Usage:
    python test_rca_with_dashboard.py
"""

import os
import sys
import time
import webbrowser

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.llm_service import LLMService
from src.rca_infotainment.dashboard.dashboard_server import RCADashboard
from src.utils.config import load_config

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    """Run RCA analysis with live dashboard"""
    
    print("\n" + "="*60)
    print("  RCA ENGINE TEST WITH LIVE DASHBOARD")
    print("="*60)
    print()
    
    # Find test DLT file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dlt_file = None
    
    # Try multiple locations
    possible_paths = [
        os.path.join(script_dir, 'data', 'dlt_logs', 'usb_str_slow.dlt'),
        os.path.join(script_dir, 'attachments', 'usb_str_slow.dlt'),
        os.path.join(script_dir, 'data', 'dlt_logs', 'audio_delay_defect.dlt'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            dlt_file = path
            break
    
    if not dlt_file:
        print("ERROR: No test DLT file found!")
        print("Tried:")
        for p in possible_paths:
            print(f"  - {p}")
        return
    
    print(f"✓ Using DLT file: {os.path.basename(dlt_file)}")
    print(f"  Size: {os.path.getsize(dlt_file):,} bytes")
    print()
    
    # Load configuration
    config = load_config('config/config.yaml')
    
    # Start dashboard
    print("Starting dashboard server...")
    dashboard = RCADashboard(port=5050)
    dashboard.start(open_browser=True)
    print(f"✓ Dashboard running at http://localhost:5050")
    print()
    
    # Wait for dashboard to start
    time.sleep(2)
    
    # Initialize RCA Engine
    print("Initializing RCA Engine...")
    rca_engine = RCAEngine(config=config)
    
    # Connect dashboard to RCA engine
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
    
    print()
    print("-"*60)
    print("STARTING RCA ANALYSIS")
    print("Watch the dashboard for live updates!")
    print("-"*60)
    print()
    
    # Run RCA analysis
    # The RCA engine will automatically update the dashboard with:
    # - Stage progress
    # - Token consumption
    # - Confidence scores
    # - Analysis results
    
    defect_id = "TEST-DASHBOARD-001"
    
    try:
        result = rca_engine.analyze_defect(
            defect_id=defect_id,
            from_jira=False,  # Use local test data
            upload_to_jira=False,  # Don't update JIRA
            mark_duplicates=False
        )
        
        print()
        print("="*60)
        print("RCA ANALYSIS COMPLETE")
        print("="*60)
        print()
        
        if result.get('status') == 'completed':
            print(f"✓ Status: SUCCESS")
            print(f"  Root Cause: {result.get('root_cause', 'N/A')[:100]}...")
            print(f"  Confidence: {result.get('confidence', 0):.0%}")
            print(f"  Domain: {result.get('domain', 'Unknown')}")
            print(f"  Duration: {result.get('duration_seconds', 0):.1f}s")
            print()
            
            # Token metrics
            token_metrics = result.get('token_metrics', {})
            if token_metrics:
                print("Token Usage:")
                print(f"  Input: {token_metrics.get('total_input', 0):,}")
                print(f"  Output: {token_metrics.get('total_output', 0):,}")
                print(f"  Total: {token_metrics.get('total_tokens', 0):,}")
                print(f"  Cost: €{token_metrics.get('estimated_cost_eur', 0):.4f}")
                print()
            
            # Reports
            reports = result.get('reports', {})
            if reports:
                print("Reports generated:")
                md_report = reports.get('markdown_report', '')
                html_report = reports.get('html_report', '')
                
                if md_report and os.path.exists(md_report):
                    print(f"  📄 Markdown: {md_report}")
                if html_report and os.path.exists(html_report):
                    print(f"  🌐 HTML: {html_report}")
                    
                    # Open HTML report in browser
                    print()
                    print("Opening HTML report in browser...")
                    webbrowser.open(f'file:///{os.path.abspath(html_report)}')
                print()
        else:
            print(f"✗ Status: FAILED")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            print()
        
    except Exception as e:
        print(f"\n✗ Error during RCA analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # Keep dashboard running
    print("-"*60)
    print("Dashboard is still running for review")
    print("Press Ctrl+C to stop")
    print("-"*60)
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
