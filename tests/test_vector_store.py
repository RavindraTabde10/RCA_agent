"""
Test script for LanceDB Vector Database
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.knowledge_layer.vector_store import VectorStore


def test_vector_store():
    """Test vector store functionality"""
    
    print("=" * 80)
    print("LanceDB Vector Store Test")
    print("=" * 80)
    
    # Initialize
    print("\n1. Initializing Vector Store...")
    vector_store = VectorStore(db_path="data/vector_db")
    print("   ✓ Initialized")
    
    # Check stats
    print("\n2. Database Statistics:")
    stats = vector_store.get_stats()
    if stats.get('indexed'):
        print(f"   ✓ Database indexed")
        print(f"   ✓ Total defects: {stats['total_defects']}")
        if stats.get('components'):
            print(f"\n   Components:")
            for comp, count in sorted(stats['components'].items()):
                print(f"     - {comp}: {count}")
    else:
        print("   ⚠ Database not indexed yet")
        print("   Run 'python build_vector_db.py' to build the database")
        return
    
    # Test searches
    print("\n3. Running Test Searches:")
    
    test_cases = [
        {
            "query": "Audio stops playing after switching sources",
            "expected_component": "AudioService"
        },
        {
            "query": "Bluetooth connection is unstable and drops",
            "expected_component": "Connectivity"
        },
        {
            "query": "System becomes slow after running for hours",
            "expected_component": "System"
        },
        {
            "query": "USB device is not recognized",
            "expected_component": "MediaService"
        },
        {
            "query": "CAN bus communication error",
            "expected_component": "Communication"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test['query']}")
        results = vector_store.search_similar_defects(test['query'], limit=3)
        
        if results:
            print(f"   ✓ Found {len(results)} similar defects:")
            for j, defect in enumerate(results, 1):
                print(f"\n     {j}. [{defect['key']}] {defect['summary']}")
                print(f"        Component: {defect['component']}")
                print(f"        Distance: {defect.get('distance', 0):.4f}")
                print(f"        Root Cause: {defect['root_cause'][:80]}...")
        else:
            print("   ✗ No results found")
    
    # Test component filter
    print("\n4. Testing Component Filter:")
    query = "Connection issues"
    component = "Connectivity"
    results = vector_store.search_similar_defects(
        query,
        limit=5,
        component_filter=component
    )
    print(f"   Query: '{query}' (Component: {component})")
    print(f"   ✓ Found {len(results)} defects in {component}")
    for defect in results[:3]:
        print(f"     - {defect['key']}: {defect['summary'][:60]}...")
    
    # Test get by key
    print("\n5. Testing Get Defect by Key:")
    test_key = "SAM1-342"
    defect = vector_store.get_defect_by_key(test_key)
    if defect:
        print(f"   ✓ Found defect {test_key}")
        print(f"     Summary: {defect['summary']}")
        print(f"     Component: {defect['component']}")
        print(f"     Status: {defect['status']}")
    else:
        print(f"   ✗ Defect {test_key} not found")
    
    print("\n" + "=" * 80)
    print("✅ All Tests Complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_vector_store()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
