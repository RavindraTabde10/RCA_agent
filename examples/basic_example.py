"""
Example: Basic defect analysis
"""

from src.main import RCAAgent


def main():
    print("="*60)
    print("RCA Agent - Basic Example")
    print("="*60)
    
    # Initialize agent
    print("\n1. Initializing RCA Agent...")
    agent = RCAAgent()
    
    # Example defect data
    defect_data = {
        "id": "EXAMPLE-001",
        "title": "Application crashes on startup",
        "description": """
        The application crashes immediately after startup on Windows 10.
        Error message shows 'Failed to initialize database connection'.
        This started happening after the latest deployment.
        """,
        "severity": "critical",
        "priority": "high",
        "timestamp": "2026-07-09T14:30:00Z",
        "logs": [
            "2026-07-09 14:30:00 ERROR - Database connection failed",
            "2026-07-09 14:30:00 ERROR - java.sql.SQLException: Connection refused",
            "2026-07-09 14:30:01 FATAL - Application shutting down"
        ],
        "environment": {
            "os": "Windows 10",
            "version": "1.2.3",
            "database": "PostgreSQL 14"
        },
        "comments": [
            {
                "author": "user1",
                "text": "This started after we updated the database driver",
                "timestamp": "2026-07-09T14:35:00Z"
            }
        ]
    }
    
    # Run analysis
    print("\n2. Analyzing defect...")
    print(f"   Defect ID: {defect_data['id']}")
    print(f"   Title: {defect_data['title']}")
    
    diagnosis = agent.analyze_defect(defect_data)
    
    # Display results
    print("\n3. Analysis Results:")
    print("="*60)
    print(f"Root Cause: {diagnosis.get('root_cause')}")
    print(f"Confidence: {diagnosis.get('confidence', 0):.1%}")
    print(f"Priority: {diagnosis.get('priority', 'N/A').upper()}")
    print(f"Assigned Team: {diagnosis.get('assigned_team', 'N/A')}")
    
    print("\nRecommendations:")
    for i, rec in enumerate(diagnosis.get('recommendations', []), 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)


if __name__ == "__main__":
    main()
