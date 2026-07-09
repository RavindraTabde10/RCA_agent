"""
Script to build LanceDB vector database from historical defects
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.knowledge_layer.vector_store import VectorStore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Build vector database from defects data"""
    
    print("=" * 80)
    print("Building LanceDB Vector Database for Historical Defects")
    print("=" * 80)
    
    # Paths
    defects_json = "data/historical_defects/defects_data.json"
    db_path = "data/vector_db"
    
    # Check if defects file exists
    if not os.path.exists(defects_json):
        print(f"\n❌ Error: Defects file not found: {defects_json}")
        print("Please ensure defects_data.json exists in data/historical_defects/")
        return 1
    
    print(f"\n📁 Defects file: {defects_json}")
    print(f"📁 Database path: {db_path}")
    
    # Initialize vector store
    print("\n1. Initializing Vector Store...")
    try:
        vector_store = VectorStore(db_path=db_path)
        print("   ✓ Vector Store initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize Vector Store: {str(e)}")
        return 1
    
    # Index defects
    print("\n2. Indexing defects (this may take a while)...")
    print("   Generating embeddings for each defect...")
    try:
        vector_store.index_defects(defects_json, batch_size=10)
        print("   ✓ All defects indexed successfully")
    except Exception as e:
        print(f"   ✗ Failed to index defects: {str(e)}")
        return 1
    
    # Get statistics
    print("\n3. Database Statistics:")
    try:
        stats = vector_store.get_stats()
        print(f"   Total defects: {stats.get('total_defects', 0)}")
        print(f"   Indexed: {stats.get('indexed', False)}")
        
        if stats.get('components'):
            print(f"\n   Components:")
            for component, count in stats['components'].items():
                print(f"     - {component}: {count} defects")
    except Exception as e:
        print(f"   ✗ Failed to get stats: {str(e)}")
    
    # Test search
    print("\n4. Testing Search...")
    test_queries = [
        "Audio playback is delayed when switching sources",
        "Bluetooth connection keeps dropping",
        "System is slow after running for a long time"
    ]
    
    for query in test_queries:
        print(f"\n   Query: \"{query}\"")
        try:
            results = vector_store.search_similar_defects(query, limit=3)
            if results:
                print(f"   Found {len(results)} similar defects:")
                for i, defect in enumerate(results, 1):
                    print(f"     {i}. {defect['key']}: {defect['summary']}")
                    print(f"        Component: {defect['component']}, Distance: {defect.get('distance', 'N/A'):.4f}")
            else:
                print("   No results found")
        except Exception as e:
            print(f"   ✗ Search failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Vector Database Build Complete!")
    print("=" * 80)
    print(f"\nDatabase location: {os.path.abspath(db_path)}")
    print("You can now use the vector store for semantic defect search.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
