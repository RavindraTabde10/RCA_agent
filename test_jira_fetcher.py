#!/usr/bin/env python3
"""
Test script for JIRA Data Fetcher - Testing attachments and DLT logs
"""

import os
import sys
from pathlib import Path
from jira_data_fetcher import JiraDataFetcher

def test_connection():
    """Test 1: Connection to JIRA"""
    print("\n" + "="*60)
    print("TEST 1: Testing JIRA Connection")
    print("="*60)
    
    try:
        fetcher = JiraDataFetcher()
        success = fetcher.test_connection()
        if success:
            print("✓ Connection test PASSED")
            return fetcher
        else:
            print("✗ Connection test FAILED")
            return None
    except Exception as e:
        print(f"✗ Connection test FAILED with error: {e}")
        return None


def test_fetch_ticket(fetcher, ticket_key="SAM1-11"):
    """Test 2: Fetch ticket data"""
    print("\n" + "="*60)
    print(f"TEST 2: Fetching Ticket {ticket_key}")
    print("="*60)
    
    try:
        ticket = fetcher.fetch_ticket(ticket_key, verbose=True)
        if ticket:
            print(f"\n✓ Ticket fetch PASSED")
            print(f"  Key: {ticket.get('key')}")
            print(f"  Summary: {ticket.get('summary')}")
            print(f"  Status: {ticket.get('status')}")
            print(f"  Labels: {ticket.get('labels')}")
            
            attachments = ticket.get('attachments', [])
            print(f"  Attachments: {len(attachments)} file(s)")
            for att in attachments:
                print(f"    - {att.get('filename')} ({att.get('size')} bytes, {att.get('mimeType')})")
            
            return ticket
        else:
            print("✗ Ticket fetch FAILED")
            return None
    except Exception as e:
        print(f"✗ Ticket fetch FAILED with error: {e}")
        return None


def test_download_all_attachments(fetcher, ticket_key="SAM1-11"):
    """Test 3: Download all attachments"""
    print("\n" + "="*60)
    print(f"TEST 3: Downloading All Attachments from {ticket_key}")
    print("="*60)
    
    dest_dir = "test_downloads/all_attachments"
    
    try:
        downloaded = fetcher.download_attachments(ticket_key, dest_dir)
        print(f"\n✓ Download all attachments PASSED")
        print(f"  Downloaded {len(downloaded)} file(s) to {dest_dir}")
        for file_path in downloaded:
            size = os.path.getsize(file_path)
            print(f"    - {Path(file_path).name} ({size} bytes)")
        return downloaded
    except Exception as e:
        print(f"✗ Download all attachments FAILED with error: {e}")
        return []


def test_download_dlt_logs(fetcher, ticket_key="SAM1-11"):
    """Test 4: Download only DLT/log files"""
    print("\n" + "="*60)
    print(f"TEST 4: Downloading DLT/Log Files from {ticket_key}")
    print("="*60)
    
    dest_dir = "test_downloads/dlt_logs_only"
    
    try:
        downloaded = fetcher.download_dlt_attachments(ticket_key, dest_dir)
        print(f"\n✓ Download DLT logs PASSED")
        print(f"  Downloaded {len(downloaded)} DLT/log file(s) to {dest_dir}")
        for file_path in downloaded:
            size = os.path.getsize(file_path)
            print(f"    - {Path(file_path).name} ({size} bytes)")
        return downloaded
    except Exception as e:
        print(f"✗ Download DLT logs FAILED with error: {e}")
        return []


def test_save_metadata(fetcher, ticket_key="SAM1-11"):
    """Test 5: Save ticket metadata"""
    print("\n" + "="*60)
    print(f"TEST 5: Saving Ticket Metadata for {ticket_key}")
    print("="*60)
    
    dest_dir = "test_downloads/metadata"
    
    try:
        meta_file = fetcher.save_ticket_metadata(ticket_key, dest_dir)
        if meta_file and os.path.exists(meta_file):
            size = os.path.getsize(meta_file)
            print(f"\n✓ Save metadata PASSED")
            print(f"  Saved to: {meta_file} ({size} bytes)")
            return meta_file
        else:
            print("✗ Save metadata FAILED")
            return None
    except Exception as e:
        print(f"✗ Save metadata FAILED with error: {e}")
        return None


def test_fetch_by_labels(fetcher):
    """Test 6: Fetch tickets by labels"""
    print("\n" + "="*60)
    print("TEST 6: Fetching Tickets by Labels")
    print("="*60)
    
    try:
        # Test with common RCA labels
        labels = ["needs-rca", "auto-rca"]
        print(f"Searching for tickets with labels: {labels}")
        
        tickets = fetcher.fetch_by_labels(labels, max_results=5)
        print(f"\n✓ Fetch by labels PASSED")
        print(f"  Found {len(tickets)} ticket(s)")
        
        for ticket in tickets[:3]:  # Show first 3
            print(f"    - {ticket.get('key')}: {ticket.get('summary')[:60]}...")
            print(f"      Labels: {ticket.get('labels')}")
        
        return tickets
    except Exception as e:
        print(f"✗ Fetch by labels FAILED with error: {e}")
        return []


def test_workspace_download(fetcher, ticket_key="SAM1-11"):
    """Test 7: Download to workspace structure (like scheduler does)"""
    print("\n" + "="*60)
    print(f"TEST 7: Download to Workspace Structure (Scheduler Mode)")
    print("="*60)
    
    workspace_dir = f"test_downloads/workspace_{ticket_key}"
    
    try:
        # First fetch the ticket
        ticket = fetcher.fetch_ticket(ticket_key, verbose=False)
        if not ticket:
            print("✗ Failed to fetch ticket")
            return []
        
        # Download using workspace structure
        downloaded = fetcher.download_ticket_attachments_to_workspace(ticket, workspace_dir)
        
        print(f"\n✓ Workspace download PASSED")
        print(f"  Downloaded {len(downloaded)} file(s)")
        print(f"  Workspace structure:")
        print(f"    {workspace_dir}/")
        print(f"      dlt_logs/")
        print(f"      attachments/")
        
        # Show what was downloaded
        dlt_logs = [f for f in downloaded if 'dlt_logs' in f]
        other_files = [f for f in downloaded if 'dlt_logs' not in f]
        
        if dlt_logs:
            print(f"\n  DLT/Log files ({len(dlt_logs)}):")
            for f in dlt_logs:
                print(f"    - {Path(f).name}")
        
        if other_files:
            print(f"\n  Other attachments ({len(other_files)}):")
            for f in other_files:
                print(f"    - {Path(f).name}")
        
        return downloaded
    except Exception as e:
        print(f"✗ Workspace download FAILED with error: {e}")
        return []


def main():
    print("\n")
    print("*" * 60)
    print("JIRA DATA FETCHER - COMPREHENSIVE TEST SUITE")
    print("Testing Attachments and DLT Logs Functionality")
    print("*" * 60)
    
    # Create test downloads directory
    os.makedirs("test_downloads", exist_ok=True)
    
    results = {}
    
    # Test 1: Connection
    fetcher = test_connection()
    results['connection'] = fetcher is not None
    if not fetcher:
        print("\n⚠ Cannot proceed without connection. Exiting.")
        sys.exit(1)
    
    # Test 2: Fetch ticket
    ticket = test_fetch_ticket(fetcher)
    results['fetch_ticket'] = ticket is not None
    
    # Test 3: Download all attachments
    all_attachments = test_download_all_attachments(fetcher)
    results['download_all'] = len(all_attachments) > 0
    
    # Test 4: Download DLT logs only
    dlt_logs = test_download_dlt_logs(fetcher)
    results['download_dlt'] = len(dlt_logs) > 0
    
    # Test 5: Save metadata
    meta_file = test_save_metadata(fetcher)
    results['save_metadata'] = meta_file is not None
    
    # Test 6: Fetch by labels
    labeled_tickets = test_fetch_by_labels(fetcher)
    results['fetch_by_labels'] = len(labeled_tickets) > 0
    
    # Test 7: Workspace download
    workspace_files = test_workspace_download(fetcher)
    results['workspace_download'] = len(workspace_files) > 0
    
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
    
    if passed_tests == total_tests:
        print("\n🎉 All tests PASSED!")
    else:
        print(f"\n⚠ {total_tests - passed_tests} test(s) FAILED")
    
    print("\nTest artifacts saved to: test_downloads/")
    print("="*60)


if __name__ == "__main__":
    main()
