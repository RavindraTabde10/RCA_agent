"""Search for available defects in KAN project"""
import os
from dotenv import load_dotenv
from jira_data_fetcher import JiraDataFetcher

load_dotenv()

def search_defects():
    """Search for all defects in KAN project"""
    print("=" * 70)
    print("  SEARCHING KAN PROJECT FOR DEFECTS")
    print("=" * 70)
    print()
    
    # Initialize JIRA client
    jira_fetcher = JiraDataFetcher()
    
    # Search 1: All open defects without RCA label
    print("Search 1: Open defects WITHOUT rca-done label")
    print("-" * 70)
    tickets = jira_fetcher.fetch_by_labels(
        labels=['needs-rca'],
        project_key='KAN',
        additional_filter='status != Closed AND status != Done'
    )
    
    # If no tickets with needs-rca, search for all open tickets
    if not tickets:
        print("No tickets with 'needs-rca' label. Searching all open defects...")
        print()
        # Search without label requirement
        try:
            # Use direct API call for broader search
            import requests
            from requests.auth import HTTPBasicAuth
            import os
            
            url = f"{os.getenv('JIRA_BASE_URL')}/rest/api/3/search/jql"
            auth = HTTPBasicAuth(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
            
            # JQL for all open bugs/defects
            jql = 'project = KAN AND status != Closed AND status != Done ORDER BY created DESC'
            
            params = {
                'jql': jql,
                'maxResults': 10,
                'fields': 'key,summary,description,status,issuetype,priority,labels'
            }
            
            response = requests.get(url, auth=auth, params=params)
            if response.status_code == 200:
                data = response.json()
                issues = data.get('issues', [])
                tickets = []
                for issue in issues:
                    fields = issue.get('fields', {})
                    tickets.append({
                        'key': issue.get('key'),
                        'summary': fields.get('summary', ''),
                        'status': fields.get('status', {}).get('name', ''),
                        'labels': fields.get('labels', []),
                        'priority': fields.get('priority', {}).get('name', 'Unknown') if fields.get('priority') else 'Unknown'
                    })
        except Exception as e:
            print(f"Error searching: {e}")
            tickets = []
    
    print(f"Found {len(tickets)} open tickets")
    for ticket in tickets:
        labels = ticket.get('labels', [])
        status = ticket.get('status', 'Unknown')
        priority = ticket.get('priority', 'Unknown')
        print(f"  • {ticket.get('key')}: {ticket.get('summary')}")
        print(f"    Status: {status} | Priority: {priority} | Labels: {labels}")
    print()
    
    return tickets

if __name__ == "__main__":
    search_defects()
