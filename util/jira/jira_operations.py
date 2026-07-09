"""
Common Jira Operations - Helper Examples
Quick reference for common Jira automation tasks
"""

from jira_automation import JiraClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize client
client = JiraClient(
    os.getenv('JIRA_URL'),
    os.getenv('JIRA_EMAIL'),
    os.getenv('JIRA_API_TOKEN')
)

PROJECT_KEY = os.getenv('PROJECT_KEY', 'KAN')


def get_all_open_bugs():
    """Get all open bugs (not Done)"""
    print(f"📋 Fetching all open bugs in {PROJECT_KEY}...")
    result = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug AND status != Done",
        max_results=100
    )
    
    print(f"Found {result['total']} open bugs")
    for issue in result['issues']:
        print(f"  {issue['key']}: {issue['fields']['summary']}")
    
    return result


def get_high_priority_bugs():
    """Get high priority bugs"""
    print(f"\n🔥 Fetching high priority bugs in {PROJECT_KEY}...")
    result = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug AND priority = High",
        max_results=100
    )
    
    print(f"Found {result['total']} high priority bugs")
    for issue in result['issues']:
        status = issue['fields']['status']['name']
        print(f"  {issue['key']}: {issue['fields']['summary']} [{status}]")
    
    return result


def get_unassigned_bugs():
    """Get unassigned bugs"""
    print(f"\n👤 Fetching unassigned bugs in {PROJECT_KEY}...")
    result = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug AND assignee is EMPTY",
        max_results=100
    )
    
    print(f"Found {result['total']} unassigned bugs")
    for issue in result['issues']:
        print(f"  {issue['key']}: {issue['fields']['summary']}")
    
    return result


def get_recently_created_bugs(days=7):
    """Get bugs created in the last N days"""
    print(f"\n📅 Fetching bugs created in the last {days} days...")
    result = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug AND created >= -{days}d",
        max_results=100
    )
    
    print(f"Found {result['total']} bugs created in the last {days} days")
    for issue in result['issues']:
        created = issue['fields']['created'][:10]
        print(f"  {issue['key']}: {issue['fields']['summary']} (Created: {created})")
    
    return result


def get_bugs_by_status(status="To Do"):
    """Get bugs by specific status"""
    print(f"\n📊 Fetching bugs with status: {status}...")
    result = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug AND status = '{status}'",
        max_results=100
    )
    
    print(f"Found {result['total']} bugs in '{status}' status")
    for issue in result['issues']:
        print(f"  {issue['key']}: {issue['fields']['summary']}")
    
    return result


def get_bug_statistics():
    """Get overall bug statistics"""
    print(f"\n📈 Bug Statistics for {PROJECT_KEY}")
    print("="*60)
    
    # Total bugs
    total = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug",
        max_results=1
    )
    print(f"Total Bugs: {total['total']}")
    
    # Open bugs
    open_bugs = client.search_with_jql(
        f"project = {PROJECT_KEY} AND issuetype = Bug AND status != Done",
        max_results=1
    )
    print(f"Open Bugs: {open_bugs['total']}")
    
    # Closed bugs
    closed = total['total'] - open_bugs['total']
    print(f"Closed Bugs: {closed}")
    
    # By priority
    priorities = ['Highest', 'High', 'Medium', 'Low', 'Lowest']
    print("\nBy Priority:")
    for priority in priorities:
        result = client.search_with_jql(
            f"project = {PROJECT_KEY} AND issuetype = Bug AND priority = {priority}",
            max_results=1
        )
        if result['total'] > 0:
            print(f"  {priority}: {result['total']}")
    
    print("="*60)


def export_all_bugs_to_csv():
    """Export all bugs to CSV file"""
    import csv
    
    print(f"\n💾 Exporting all bugs to CSV...")
    result = client.search_bugs(project_key=PROJECT_KEY, max_results=1000)
    
    filename = f'{PROJECT_KEY}_bugs_export.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Key', 'Summary', 'Status', 'Priority', 'Assignee', 'Reporter', 'Created', 'Updated'])
        
        # Data
        for issue in result['issues']:
            fields = issue['fields']
            assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
            reporter = fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown'
            
            writer.writerow([
                issue['key'],
                fields.get('summary', ''),
                fields.get('status', {}).get('name', ''),
                fields.get('priority', {}).get('name', ''),
                assignee,
                reporter,
                fields.get('created', '')[:10],
                fields.get('updated', '')[:10]
            ])
    
    print(f"✅ Exported {len(result['issues'])} bugs to {filename}")


def main():
    """Run common operations"""
    try:
        print("🚀 Jira Bug Analysis Tool")
        print("="*60)
        
        # Run various analyses
        get_bug_statistics()
        get_all_open_bugs()
        get_high_priority_bugs()
        get_unassigned_bugs()
        get_recently_created_bugs(days=7)
        
        # Export to CSV
        export_all_bugs_to_csv()
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
