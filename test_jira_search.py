#!/usr/bin/env python3
"""Test JIRA search functionality"""

from jira_data_fetcher import JiraDataFetcher

# Initialize fetcher
fetcher = JiraDataFetcher()

# Test 1: Fetch single ticket (should work)
print("=" * 60)
print("TEST 1: Fetch single ticket")
print("=" * 60)
ticket = fetcher.fetch_ticket('SAM1-11')
if ticket:
    print(f"✓ SUCCESS: {ticket['key']} - {ticket['summary']}")
else:
    print("✗ FAILED: Could not fetch ticket")

# Test 2: Search by labels (debugging the 410 error)
print("\n" + "=" * 60)
print("TEST 2: Search by labels")
print("=" * 60)
tickets = fetcher.fetch_by_labels(
    labels=['needs-rca'],
    project_key='SAM1',
    additional_filter='status != Closed AND status != Done',
    max_results=10
)
print(f"Found {len(tickets)} tickets")

# Test 3: Try simpler JQL
print("\n" + "=" * 60)
print("TEST 3: Search with simpler JQL")
print("=" * 60)
tickets = fetcher.fetch_by_labels(
    labels=['needs-rca'],
    project_key='SAM1',
    max_results=10
)
print(f"Found {len(tickets)} tickets")
