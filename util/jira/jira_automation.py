"""
Jira Bug Fetcher Script
This script fetches bug details from Jira using the REST API.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class JiraClient:
    """Client for interacting with Jira REST API"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Jira client
        
        Args:
            base_url: Jira instance URL (e.g., https://yourinstance.atlassian.net)
            email: Your Atlassian account email
            api_token: Your Jira API token
        """
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to Jira API"""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            auth=self.auth,
            **kwargs
        )
        response.raise_for_status()
        return response
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects in the Jira instance"""
        response = self._make_request('GET', '/rest/api/3/project')
        return response.json()
    
    def get_issue(self, issue_key: str) -> Dict:
        """
        Get details of a specific issue
        
        Args:
            issue_key: Issue key (e.g., 'KAN-123')
        """
        response = self._make_request('GET', f'/rest/api/3/issue/{issue_key}')
        return response.json()
    
    def search_bugs(self, project_key: str = None, max_results: int = 50) -> Dict:
        """
        Search for bugs in Jira
        
        Args:
            project_key: Optional project key to filter by
            max_results: Maximum number of results to return
        """
        # Build JQL query to search for bugs
        jql_parts = ["issuetype = Bug"]
        
        if project_key:
            jql_parts.insert(0, f"project = {project_key}")
        
        jql = " AND ".join(jql_parts)
        
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'summary,status,priority,assignee,reporter,created,updated,description'
        }
        
        response = self._make_request('GET', '/rest/api/3/search', params=params)
        return response.json()
    
    def search_with_jql(self, jql: str, max_results: int = 50) -> Dict:
        """
        Search issues using custom JQL query
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results
        """
        params = {
            'jql': jql,
            'maxResults': max_results
        }
        
        response = self._make_request('GET', '/rest/api/3/search', params=params)
        return response.json()
    
    def get_board_issues(self, board_id: int) -> Dict:
        """
        Get all issues from a specific board
        
        Args:
            board_id: The board ID
        """
        response = self._make_request('GET', f'/rest/agile/1.0/board/{board_id}/issue')
        return response.json()


def format_bug_output(bug: Dict) -> None:
    """Format and print bug details"""
    fields = bug.get('fields', {})
    
    print(f"\n{'='*80}")
    print(f"Issue Key: {bug.get('key', 'N/A')}")
    print(f"Summary: {fields.get('summary', 'N/A')}")
    print(f"Status: {fields.get('status', {}).get('name', 'N/A')}")
    print(f"Priority: {fields.get('priority', {}).get('name', 'N/A')}")
    
    assignee = fields.get('assignee')
    if assignee:
        print(f"Assignee: {assignee.get('displayName', 'N/A')}")
    else:
        print("Assignee: Unassigned")
    
    reporter = fields.get('reporter')
    if reporter:
        print(f"Reporter: {reporter.get('displayName', 'N/A')}")
    
    print(f"Created: {fields.get('created', 'N/A')}")
    print(f"Updated: {fields.get('updated', 'N/A')}")
    
    description = fields.get('description')
    if description:
        # For Atlassian Document Format
        if isinstance(description, dict):
            print(f"Description: [Rich content - view in Jira]")
        else:
            print(f"Description: {description[:200]}...")
    
    print(f"{'='*80}")


def main():
    """Main function to fetch and display Jira bugs"""
    
    # Load credentials from environment variables
    JIRA_URL = os.getenv('JIRA_URL', 'https://ravindratabde10.atlassian.net')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    PROJECT_KEY = os.getenv('PROJECT_KEY', 'KAN')
    
    # Validate credentials
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        print("Error: JIRA_EMAIL and JIRA_API_TOKEN must be set in .env file")
        print("Please create a .env file with your credentials")
        return
    
    try:
        # Initialize Jira client
        print(f"Connecting to Jira: {JIRA_URL}")
        client = JiraClient(JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)
        
        # Fetch all bugs from the project
        print(f"\nFetching bugs from project: {PROJECT_KEY}")
        result = client.search_bugs(project_key=PROJECT_KEY, max_results=100)
        
        bugs = result.get('issues', [])
        total = result.get('total', 0)
        
        print(f"\nFound {total} bug(s) in project {PROJECT_KEY}")
        print(f"Displaying {len(bugs)} bug(s)")
        
        # Display each bug
        for bug in bugs:
            format_bug_output(bug)
        
        # Save to JSON file
        output_file = 'jira_bugs.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Full results saved to {output_file}")
        
        # Additional examples
        print("\n" + "="*80)
        print("OTHER AVAILABLE QUERIES:")
        print("="*80)
        
        # Example: Get specific issue
        if bugs:
            first_bug_key = bugs[0].get('key')
            print(f"\nExample: Fetching specific issue {first_bug_key}")
            issue = client.get_issue(first_bug_key)
            print(f"✓ Successfully fetched issue: {issue['fields']['summary']}")
        
        # Example: Custom JQL query
        print("\nExample: Custom JQL - Open bugs with high priority")
        custom_result = client.search_with_jql(
            f"project = {PROJECT_KEY} AND issuetype = Bug AND status != Done AND priority = High",
            max_results=10
        )
        print(f"✓ Found {custom_result['total']} high priority open bugs")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
