"""
Test script for Vector Database Integration with RCA Agents
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processing_layer.agents.pattern_agent import PatternAgent
from src.processing_layer.reasoning.hypothesis_generator import HypothesisGenerator


def test_pattern_agent():
    """Test Pattern Agent with vector database"""
    print("=" * 80)
    print("Testing Pattern Agent with Vector Database Integration")
    print("=" * 80)
    
    # Initialize Pattern Agent
    print("\n1. Initializing Pattern Agent...")
    pattern_agent = PatternAgent()
    print("   ✓ Pattern Agent initialized")
    
    # Test defect
    test_defect = {
        "description": "Audio playback stops working after switching from Bluetooth to USB source",
        "component": "AudioService",
        "severity": "high"
    }
    
    print(f"\n2. Test Defect:")
    print(f"   Description: {test_defect['description']}")
    print(f"   Component: {test_defect['component']}")
    
    # Analyze defect
    print("\n3. Analyzing with Pattern Agent...")
    results = pattern_agent.analyze(test_defect, historical_data=[])
    
    print(f"\n4. Results:")
    print(f"   Pattern Type: {results.get('pattern_type')}")
    print(f"   Confidence: {results.get('confidence'):.2f}")
    print(f"   Matched Patterns: {len(results.get('matched_patterns', []))}")
    print(f"   Similar Defects: {len(results.get('similar_defects', []))}")
    
    # Show similar defects
    if results.get('similar_defects'):
        print("\n   Top 3 Similar Historical Defects:")
        for i, similar in enumerate(results['similar_defects'][:3], 1):
            defect = similar.get('defect', {})
            print(f"\n     {i}. [{defect.get('key')}] {defect.get('description', 'N/A')[:60]}...")
            print(f"        Component: {defect.get('component')}")
            print(f"        Similarity Score: {similar.get('similarity_score', 0):.4f}")
            print(f"        Distance: {similar.get('distance', 'N/A')}")
            if defect.get('root_cause'):
                print(f"        Root Cause: {defect.get('root_cause')[:80]}...")
    
    # Show recommendations
    if results.get('recommendations'):
        print("\n5. Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    print("\n" + "=" * 80)


def test_hypothesis_generator():
    """Test Hypothesis Generator with vector database"""
    print("\nTesting Hypothesis Generator with Vector Database Integration")
    print("=" * 80)
    
    # Initialize Hypothesis Generator
    print("\n1. Initializing Hypothesis Generator...")
    hypothesis_gen = HypothesisGenerator()
    print("   ✓ Hypothesis Generator initialized")
    
    # Test defect
    test_defect = {
        "description": "Bluetooth connection drops frequently during phone calls",
        "component": "Connectivity",
        "severity": "high"
    }
    
    print(f"\n2. Test Defect:")
    print(f"   Description: {test_defect['description']}")
    print(f"   Component: {test_defect['component']}")
    
    # Generate hypotheses
    print("\n3. Generating Hypotheses...")
    evidence = [
        {
            "type": "error",
            "component": "Connectivity",
            "description": "Bluetooth service crashed"
        }
    ]
    
    hypotheses = hypothesis_gen.generate_hypotheses(
        defect_data=test_defect,
        evidence=evidence
    )
    
    print(f"\n4. Generated {len(hypotheses)} Hypotheses:")
    
    # Group by source
    sources = {}
    for h in hypotheses:
        source = h.get('source', 'unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(h)
    
    for source, hyps in sources.items():
        print(f"\n   From {source.upper()} ({len(hyps)} hypotheses):")
        for i, h in enumerate(hyps, 1):
            print(f"\n     {i}. {h.get('hypothesis')[:100]}...")
            print(f"        Confidence: {h.get('confidence', 0):.2f}")
            if h.get('reasoning'):
                print(f"        Reasoning: {h.get('reasoning')[:80]}...")
            if h.get('supporting_evidence'):
                evidence = h['supporting_evidence'][0]
                if evidence.get('type') == 'historical_defect':
                    print(f"        Historical Defect: {evidence.get('defect_key')} (distance: {evidence.get('similarity_distance', 0):.4f})")
    
    print("\n" + "=" * 80)


def test_end_to_end():
    """Test end-to-end scenario"""
    print("\nEnd-to-End Integration Test")
    print("=" * 80)
    
    # Test defect
    test_defect = {
        "description": "Navigation audio guidance volume is too low compared to music",
        "component": "AudioService",
        "severity": "medium",
        "actual_behavior": "Navigation voice is barely audible when music is playing"
    }
    
    print(f"\n1. Test Defect:")
    print(f"   Description: {test_defect['description']}")
    print(f"   Component: {test_defect['component']}")
    print(f"   Severity: {test_defect['severity']}")
    
    # Step 1: Pattern Analysis
    print("\n2. Step 1: Pattern Analysis...")
    pattern_agent = PatternAgent()
    pattern_results = pattern_agent.analyze(test_defect, historical_data=[])
    
    print(f"   ✓ Found {len(pattern_results.get('similar_defects', []))} similar defects")
    
    # Step 2: Hypothesis Generation
    print("\n3. Step 2: Hypothesis Generation...")
    hypothesis_gen = HypothesisGenerator()
    
    # Use pattern results as evidence
    evidence = []
    for similar in pattern_results.get('similar_defects', [])[:3]:
        defect = similar.get('defect', {})
        evidence.append({
            "type": "historical_defect",
            "description": f"Similar defect: {defect.get('key')}",
            "root_cause": defect.get('root_cause', ''),
            "similarity": similar.get('similarity_score', 0)
        })
    
    hypotheses = hypothesis_gen.generate_hypotheses(
        defect_data=test_defect,
        evidence=evidence
    )
    
    print(f"   ✓ Generated {len(hypotheses)} hypotheses")
    
    # Show top hypotheses
    print("\n4. Top 3 Root Cause Hypotheses:")
    sorted_hypotheses = sorted(hypotheses, key=lambda x: x.get('confidence', 0), reverse=True)
    for i, h in enumerate(sorted_hypotheses[:3], 1):
        print(f"\n   {i}. {h.get('hypothesis')[:100]}...")
        print(f"      Confidence: {h.get('confidence', 0):.2f}")
        print(f"      Source: {h.get('source')}")
        if h.get('reasoning'):
            print(f"      Reasoning: {h.get('reasoning')[:80]}...")
    
    print("\n" + "=" * 80)
    print("✅ End-to-End Integration Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        # Test Pattern Agent
        test_pattern_agent()
        
        # Test Hypothesis Generator
        test_hypothesis_generator()
        
        # Test End-to-End
        test_end_to_end()
        
        print("\n" + "=" * 80)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
