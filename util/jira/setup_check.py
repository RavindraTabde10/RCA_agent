"""
Quick setup and test script for Jira automation
Run this after setting up your .env file
"""

import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    try:
        import requests
        print("✓ requests installed")
    except ImportError:
        print("❌ requests not installed")
        print("   Run: pip install requests")
        return False
    
    try:
        import dotenv
        print("✓ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Run: pip install python-dotenv")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\nChecking .env file...")
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Create .env file from .env.example:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your Jira credentials")
        return False
    
    print("✓ .env file exists")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_') or value == '':
            missing.append(var)
        else:
            print(f"✓ {var} is set")
    
    if missing:
        print(f"\n❌ Missing or invalid variables: {', '.join(missing)}")
        print("   Please update your .env file with actual values")
        return False
    
    return True

def test_connection():
    """Test connection to Jira"""
    print("\nTesting Jira connection...")
    try:
        from jira_automation import JiraClient
        from dotenv import load_dotenv
        
        load_dotenv()
        
        client = JiraClient(
            os.getenv('JIRA_URL'),
            os.getenv('JIRA_EMAIL'),
            os.getenv('JIRA_API_TOKEN')
        )
        
        # Try to get projects
        projects = client.get_all_projects()
        print(f"✓ Successfully connected to Jira!")
        print(f"  Found {len(projects)} project(s)")
        
        for project in projects[:3]:  # Show first 3
            print(f"  - {project['key']}: {project['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Verify your JIRA_URL is correct")
        print("  2. Check your JIRA_EMAIL")
        print("  3. Ensure your JIRA_API_TOKEN is valid and not expired")
        print("  4. Verify you have access to the Jira instance")
        return False

def main():
    print("="*60)
    print("Jira Automation Setup Check")
    print("="*60)
    
    if not check_dependencies():
        print("\n⚠️  Install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    if not check_env_file():
        print("\n⚠️  Set up your .env file first")
        sys.exit(1)
    
    if not test_connection():
        print("\n⚠️  Fix connection issues before proceeding")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Setup complete! You're ready to use the script.")
    print("="*60)
    print("\nRun the main script:")
    print("  python jira_automation.py")

if __name__ == "__main__":
    main()
