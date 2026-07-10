#!/usr/bin/env python
"""
Test Semantic Similarity Search with LanceDB

This script demonstrates:
1. Semantic search using local embedding model (all-MiniLM-L6-v2)
2. Similarity score calculation (0-1 scale)
3. Comparison with keyword-based search
4. Duplicate detection based on similarity thresholds
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.knowledge_layer.vector_store import VectorStore
from src.rca_infotainment.historical_matcher import HistoricalMatcher
from src.utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_results(results, title="Search Results", show_details=True):
    """Print search results in a formatted way"""
    print(f"\n{title}")
    print_separator("-", 80)
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['defect_id']}: {result['summary']}")
        print(f"   Component: {result['component']}")
        
        # Show similarity score
        similarity = result.get('similarity_score', 0)
        distance = result.get('distance', 0)
        search_type = result.get('search_type', 'unknown')
        
        print(f"   Similarity: {similarity:.2%} (score: {similarity:.4f})")
        if distance:
            print(f"   Distance: {distance:.4f}")
        print(f"   Search Type: {search_type}")
        
        # Show duplicate/related status
        if result.get('is_duplicate'):
            print(f"   ⚠️  DUPLICATE (≥90% similar)")
        elif result.get('is_related'):
            print(f"   🔗 RELATED (≥75% similar)")
        
        # Show root cause if available
        if show_details and result.get('root_cause'):
            root_cause = result['root_cause']
            if len(root_cause) > 150:
                root_cause = root_cause[:150] + "..."
            print(f"   Root Cause: {root_cause}")


def test_vector_store_direct():
    """Test VectorStore directly"""
    print_separator()
    print("TEST 1: Direct Vector Store Search")
    print_separator()
    
    try:
        # Initialize vector store
        vector_store = VectorStore(db_path="data/vector_db")
        
        # Test queries
        queries = [
            "Bluetooth keeps disconnecting from my phone",
            "Audio is delayed when I change sources",
            "System becomes very slow after using for a while",
            "Radio cannot tune to FM stations",
            "USB device not recognized after STR",
            "Bluetooth pairing fails with Android 13"
        ]
        
        for query in queries:
            print(f"\n📝 Query: \"{query}\"")
            results = vector_store.search_similar_defects(query, limit=3)
            
            if results:
                for i, defect in enumerate(results, 1):
                    similarity = defect.get('similarity_score', 0)
                    distance = defect.get('distance', 0)
                    print(f"   {i}. {defect['key']}: {defect['summary']}")
                    print(f"      Similarity: {similarity:.2%}, Distance: {distance:.4f}")
            else:
                print("   No results found")
        
        return True
        
    except Exception as e:
        logger.error(f"Vector store test failed: {e}")
        return False


def test_historical_matcher():
    """Test HistoricalMatcher with semantic search"""
    print_separator()
    print("TEST 2: Historical Matcher (Semantic Search)")
    print_separator()
    
    try:
        # Load config
        config = load_config("config/config.yaml")
        matcher = HistoricalMatcher(config)
        
        # Test semantic search
        queries = [
            "Bluetooth audio cuts out randomly",
            "Memory leak in media player",
            "CAN bus timeout error"
        ]
        
        for query in queries:
            print(f"\n📝 Query: \"{query}\"")
            results = matcher.semantic_search(query, max_results=5)
            
            if results:
                print(f"   Found {len(results)} matches:")
                for i, match in enumerate(results, 1):
                    similarity = match.get('similarity_score', 0)
                    search_type = match.get('search_type', 'unknown')
                    print(f"   {i}. [{similarity:.2%}] {match['defect_id']}: {match['summary'][:60]}...")
                    print(f"      Type: {search_type}, Component: {match['component']}")
            else:
                print("   No results found")
        
        return True
        
    except Exception as e:
        logger.error(f"Historical matcher test failed: {e}")
        return False


def test_duplicate_detection():
    """Test duplicate detection based on semantic similarity"""
    print_separator()
    print("TEST 3: Duplicate Detection")
    print_separator()
    
    try:
        config = load_config("config/config.yaml")
        matcher = HistoricalMatcher(config)
        
        # Simulate defect data
        test_defects = [
            {
                "summary": "Bluetooth audio streaming cuts out intermittently",
                "description": "Audio stops playing randomly during Bluetooth streaming",
                "component": "Connectivity"
            },
            {
                "summary": "USB device not detected after STR cycle",
                "description": "USB storage device fails to mount after suspend/resume",
                "component": "MediaService"
            },
            {
                "summary": "Memory usage grows continuously during playback",
                "description": "System memory keeps increasing when playing media files",
                "component": "MediaService"
            }
        ]
        
        for defect in test_defects:
            print(f"\n📋 Testing: \"{defect['summary']}\"")
            print(f"   Component: {defect['component']}")
            
            # Search for similar defects
            results = matcher.search(defect, max_results=3)
            
            if results:
                top_match = results[0]
                similarity = top_match['similarity_score']
                
                print(f"\n   Top Match: {top_match['defect_id']}")
                print(f"   Similarity: {similarity:.2%}")
                print(f"   Summary: {top_match['summary'][:70]}...")
                
                if top_match.get('is_duplicate'):
                    print(f"   ⚠️  DUPLICATE DETECTED (threshold: 90%)")
                elif top_match.get('is_related'):
                    print(f"   🔗 RELATED DEFECT (threshold: 75%)")
                else:
                    print(f"   ℹ️  Similar but not duplicate")
        
        return True
        
    except Exception as e:
        logger.error(f"Duplicate detection test failed: {e}")
        return False


def test_similarity_thresholds():
    """Test similarity score thresholds"""
    print_separator()
    print("TEST 4: Similarity Thresholds Analysis")
    print_separator()
    
    try:
        vector_store = VectorStore(db_path="data/vector_db")
        
        # Test query
        query = "Audio playback issue with Bluetooth"
        print(f"\n📝 Query: \"{query}\"")
        
        results = vector_store.search_similar_defects(query, limit=10)
        
        # Categorize by similarity
        duplicates = []
        related = []
        similar = []
        
        for result in results:
            similarity = result['similarity_score']
            if similarity >= 0.90:
                duplicates.append(result)
            elif similarity >= 0.75:
                related.append(result)
            elif similarity >= 0.50:
                similar.append(result)
        
        print(f"\n   Results breakdown (out of {len(results)}):")
        print(f"   ⚠️  Duplicates (≥90%): {len(duplicates)}")
        print(f"   🔗 Related (≥75%): {len(related)}")
        print(f"   ℹ️  Similar (≥50%): {len(similar)}")
        
        # Show top results with categories
        print(f"\n   Top 5 Results:")
        for i, result in enumerate(results[:5], 1):
            similarity = result['similarity_score']
            category = "DUPLICATE" if similarity >= 0.90 else "RELATED" if similarity >= 0.75 else "SIMILAR"
            print(f"   {i}. [{category} {similarity:.2%}] {result['key']}")
            print(f"      {result['summary'][:65]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Threshold analysis failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SEMANTIC SIMILARITY TESTING")
    print("Using: all-MiniLM-L6-v2 (384-dimensional embeddings)")
    print("="*80)
    
    # Check if vector DB exists
    if not os.path.exists("data/vector_db"):
        print("\n❌ Vector database not found!")
        print("Please run: python build_vector_db.py")
        return 1
    
    tests = [
        ("Direct Vector Store", test_vector_store_direct),
        ("Historical Matcher", test_historical_matcher),
        ("Duplicate Detection", test_duplicate_detection),
        ("Similarity Thresholds", test_similarity_thresholds)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n")
            success = test_func()
            results[test_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = f"❌ CRASHED: {str(e)}"
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, result in results.items():
        print(f"{result} - {test_name}")
    
    print("\n" + "="*80)
    print("SEMANTIC SIMILARITY FEATURES:")
    print("="*80)
    print("✅ Local embedding model (no API calls)")
    print("✅ 384-dimensional vectors (all-MiniLM-L6-v2)")
    print("✅ L2 distance → Similarity score conversion")
    print("✅ Similarity range: 0.0 (different) to 1.0 (identical)")
    print("✅ Duplicate threshold: ≥90% similarity")
    print("✅ Related threshold: ≥75% similarity")
    print("✅ Component filtering support")
    print("✅ Fallback to keyword search if vector DB unavailable")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
