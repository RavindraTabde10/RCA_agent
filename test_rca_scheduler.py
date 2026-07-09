#!/usr/bin/env python3
"""
Test RCA Scheduler with JIRA Data Fetcher Integration

Tests:
1. Scheduler initialization
2. JIRA connection through scheduler
3. Fetch tickets by labels
4. Workspace creation
5. Attachment download via scheduler
6. Full RCA process (dry-run)
"""

import os
import sys
import json
from pathlib import Path

# Add to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rca_scheduler import RCAScheduler


def test_scheduler_init():
    """Test 1: Scheduler initialization"""
    print("\n" + "="*60)
    print("TEST 1: Scheduler Initialization")
    print("="*60)
    
    try:
        scheduler = RCAScheduler(dry_run=True)
        print("✓ Scheduler initialized successfully")
        print(f"  Trigger labels: {scheduler.scheduler_config['trigger_labels']}")
        print(f"  Completion label: {scheduler.scheduler_config['completion_label']}")
        print(f"  Dry run mode: {scheduler.dry_run}")
        return scheduler
    except Exception as e:
        print(f"✗ Scheduler initialization FAILED: {e}")
        return None


def test_jira_connection(scheduler):
    """Test 2: JIRA connection through scheduler"""
    print("\n" + "="*60)
    print("TEST 2: JIRA Connection")
    print("="*60)
    
    if not scheduler.jira_fetcher:
        print("✗ JIRA fetcher not initialized")
        return False
    
    try:
        connected = scheduler.jira_fetcher.test_connection()
        if connected:
            print("✓ JIRA connection successful")
            return True
        else:
            print("✗ JIRA connection failed")
            return False
    except Exception as e:
        print(f"✗ JIRA connection test FAILED: {e}")
        return False


def test_fetch_tickets(scheduler):
    """Test 3: Fetch tickets by labels"""
    print("\n" + "="*60)
    print("TEST 3: Fetch Tickets by Labels")
    print("="*60)
    
    try:
        labels = ['needs-rca', 'auto-rca']
        tickets = scheduler.fetch_tickets_by_label(labels)
        
        print(f"✓ Fetch successful")
        print(f"  Found {len(tickets)} ticket(s) with labels: {labels}")
        
        for ticket in tickets:
            print(f"\n  Ticket: {ticket.get('key')}")
            print(f"    Summary: {ticket.get('summary', 'N/A')[:60]}...")
            print(f"    Status: {ticket.get('status', 'N/A')}")
            print(f"    Labels: {ticket.get('labels', [])}")
            
            attachments = ticket.get('attachments', [])
            print(f"    Attachments: {len(attachments)} file(s)")
            for att in attachments:
                print(f"      - {att.get('filename')} ({att.get('size')} bytes)")
        
        return tickets
    except Exception as e:
        print(f"✗ Fetch tickets FAILED: {e}")
        return []


def test_workspace_creation(scheduler, issue_key="SAM1-22"):
    """Test 4: Workspace creation"""
    print("\n" + "="*60)
    print("TEST 4: Workspace Creation")
    print("="*60)
    
    try:
        workspace = scheduler._create_ticket_workspace(issue_key)
        print(f"✓ Workspace created: {workspace}")
        
        # Check subdirectories
        subdirs = ['dlt_logs', 'reports', 'attachments']
        for subdir in subdirs:
            path = os.path.join(workspace, subdir)
            exists = os.path.exists(path)
            status = "✓" if exists else "✗"
            print(f"  {status} {subdir}/ : {path}")
        
        return workspace
    except Exception as e:
        print(f"✗ Workspace creation FAILED: {e}")
        return None


def test_attachment_download(scheduler, ticket):
    """Test 5: Download attachments via scheduler"""
    print("\n" + "="*60)
    print("TEST 5: Attachment Download via Scheduler")
    print("="*60)
    
    if not ticket:
        print("✗ No ticket provided")
        return []
    
    issue_key = ticket.get('key')
    try:
        workspace = scheduler._create_ticket_workspace(issue_key)
        
        # Use scheduler's download method
        downloaded = scheduler._download_ticket_attachments(ticket, workspace)
        
        print(f"✓ Download completed")
        print(f"  Workspace: {workspace}")
        print(f"  Downloaded {len(downloaded)} file(s)")
        
        for file_path in downloaded:
            size = os.path.getsize(file_path)
            rel_path = os.path.relpath(file_path, workspace)
            print(f"    - {rel_path} ({size} bytes)")
        
        # Verify files are in correct folders
        dlt_logs_dir = os.path.join(workspace, 'dlt_logs')
        dlt_files = list(Path(dlt_logs_dir).glob('*.*'))
        print(f"\n  DLT logs folder: {len(dlt_files)} file(s)")
        for dlt_file in dlt_files:
            print(f"    - {dlt_file.name}")
        
        return downloaded
    except Exception as e:
        print(f"✗ Attachment download FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_engine_configuration(scheduler):
    """Test 6: Engine configuration for ticket workspace"""
    print("\n" + "="*60)
    print("TEST 6: RCA Engine Configuration")
    print("="*60)
    
    try:
        workspace = scheduler._create_ticket_workspace("TEST-999")
        
        # Store original paths
        original_dlt_dir = scheduler.rca_engine.dlt_logs_dir
        original_output_dir = scheduler.rca_engine.output_dir
        
        print(f"Original paths:")
        print(f"  DLT logs: {original_dlt_dir}")
        print(f"  Output: {original_output_dir}")
        
        # Configure for ticket workspace
        scheduler._configure_engine_for_ticket(workspace)
        
        print(f"\nTicket workspace paths:")
        print(f"  DLT logs: {scheduler.rca_engine.dlt_logs_dir}")
        print(f"  Output: {scheduler.rca_engine.output_dir}")
        
        # Verify paths changed
        dlt_changed = scheduler.rca_engine.dlt_logs_dir != original_dlt_dir
        output_changed = scheduler.rca_engine.output_dir != original_output_dir
        
        if dlt_changed and output_changed:
            print(f"\n✓ Engine paths configured correctly")
        else:
            print(f"\n✗ Engine paths not changed")
            return False
        
        # Restore original paths
        scheduler.rca_engine.dlt_logs_dir = original_dlt_dir
        scheduler.rca_engine.output_dir = original_output_dir
        
        print(f"✓ Original paths restored")
        return True
    except Exception as e:
        print(f"✗ Engine configuration FAILED: {e}")
        return False


def test_full_rca_process(scheduler, ticket):
    """Test 7: Full RCA process (dry-run)"""
    print("\n" + "="*60)
    print("TEST 7: Full RCA Process (Dry Run)")
    print("="*60)
    
    if not ticket:
        print("✗ No ticket provided")
        return None
    
    try:
        result = scheduler.process_ticket(ticket)
        
        print(f"✓ RCA process completed")
        print(f"  Issue: {result.get('issue_key')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Workspace: {result.get('workspace')}")
        
        if result.get('status') == 'success':
            print(f"  Root Cause: {result.get('root_cause', 'N/A')[:100]}...")
            print(f"  Confidence: {result.get('confidence', 0):.0%}")
            
            if result.get('is_duplicate'):
                print(f"  ⚠️ Duplicate of: {result.get('duplicate_of')}")
        elif result.get('status') == 'error':
            print(f"  Error: {result.get('error', 'Unknown')}")
        
        return result
    except Exception as e:
        print(f"✗ Full RCA process FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_scheduler_run_once(scheduler):
    """Test 8: Scheduler run_once method"""
    print("\n" + "="*60)
    print("TEST 8: Scheduler Run Once")
    print("="*60)
    
    try:
        run_summary = scheduler.run_once()
        
        print(f"✓ Scheduler run completed")
        print(f"  Run number: {run_summary.get('run_number')}")
        print(f"  Tickets found: {run_summary.get('tickets_found', 0)}")
        print(f"  Tickets processed: {len(run_summary.get('tickets', []))}")
        
        for ticket_result in run_summary.get('tickets', []):
            print(f"\n  {ticket_result.get('issue_key')}:")
            print(f"    Status: {ticket_result.get('status')}")
            if ticket_result.get('status') == 'success':
                print(f"    Confidence: {ticket_result.get('confidence', 0):.0%}")
        
        return run_summary
    except Exception as e:
        print(f"✗ Scheduler run FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n")
    print("*" * 60)
    print("RCA SCHEDULER - COMPREHENSIVE TEST SUITE")
    print("Testing JIRA Data Fetcher Integration")
    print("*" * 60)
    
    results = {}
    
    # Test 1: Initialization
    scheduler = test_scheduler_init()
    results['init'] = scheduler is not None
    if not scheduler:
        print("\n⚠ Cannot proceed without scheduler. Exiting.")
        sys.exit(1)
    
    # Test 2: JIRA Connection
    jira_ok = test_jira_connection(scheduler)
    results['jira_connection'] = jira_ok
    if not jira_ok:
        print("\n⚠ Cannot proceed without JIRA. Exiting.")
        sys.exit(1)
    
    # Test 3: Fetch tickets
    tickets = test_fetch_tickets(scheduler)
    results['fetch_tickets'] = len(tickets) > 0
    
    # Use first ticket with attachments for remaining tests
    test_ticket = None
    for ticket in tickets:
        if ticket.get('attachments'):
            test_ticket = ticket
            break
    
    if not test_ticket and tickets:
        test_ticket = tickets[0]  # Use first ticket even without attachments
    
    # Test 4: Workspace creation
    workspace = test_workspace_creation(scheduler, test_ticket.get('key') if test_ticket else 'TEST-001')
    results['workspace_creation'] = workspace is not None
    
    # Test 5: Attachment download
    if test_ticket:
        downloaded = test_attachment_download(scheduler, test_ticket)
        results['attachment_download'] = len(downloaded) > 0
    else:
        print("\n⚠ Skipping attachment download test - no test ticket")
        results['attachment_download'] = False
    
    # Test 6: Engine configuration
    engine_ok = test_engine_configuration(scheduler)
    results['engine_config'] = engine_ok
    
    # Test 7: Full RCA process
    if test_ticket:
        rca_result = test_full_rca_process(scheduler, test_ticket)
        results['full_rca'] = rca_result is not None
    else:
        print("\n⚠ Skipping full RCA test - no test ticket")
        results['full_rca'] = False
    
    # Test 8: Scheduler run_once
    # Commented out to avoid double processing
    # run_summary = test_scheduler_run_once(scheduler)
    # results['scheduler_run'] = run_summary is not None
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:<25} {status}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    # Final statistics
    print("\n" + "="*60)
    print("SCHEDULER STATISTICS")
    print("="*60)
    stats = scheduler.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests PASSED!")
    else:
        print(f"\n⚠ {total_tests - passed_tests} test(s) FAILED")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
