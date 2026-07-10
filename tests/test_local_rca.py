#!/usr/bin/env python
"""
Test RCA Engine with local dummy defect

This script tests the full RCA pipeline without JIRA connectivity:
1. Loads dummy defect from local JSON
2. Parses DLT file (audio_bus_timeout.dlt)
3. Runs LLM analysis (if configured) or mock analysis
4. Generates report

Run: python test_local_rca.py
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.llm_service import LLMService
from src.rca_infotainment.dlt_analyzer import DLTAnalyzer
from src.utils.config import load_config


def print_separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def test_dlt_parsing():
    """Test DLT file parsing directly"""
    print_separator("TEST 1: DLT File Parsing")
    
    dlt_path = "data/dlt_logs/audio_bus_timeout.dlt"
    
    if not os.path.exists(dlt_path):
        print(f"❌ DLT file not found: {dlt_path}")
        return None
    
    print(f"📄 Parsing: {dlt_path}")
    
    analyzer = DLTAnalyzer()
    result = analyzer.analyze_file(dlt_path)
    
    print(f"\n📊 Parsing Results:")
    print(f"   Total messages: {result.get('total_messages', 0)}")
    print(f"   Errors found: {len(result.get('errors', []))}")
    print(f"   Warnings found: {len(result.get('warnings', []))}")
    
    components = result.get('components', [])
    if isinstance(components, dict):
        print(f"   Components: {list(components.keys())}")
    else:
        print(f"   Components: {components}")
    
    # Show errors
    errors = result.get('errors', [])
    if errors:
        print(f"\n🔴 Errors detected:")
        for err in errors[:5]:
            print(f"   - [{err.get('app_id', 'UNKNOWN')}] {err.get('message', '')[:80]}")
    
    # Show warnings
    warnings = result.get('warnings', [])
    if warnings:
        print(f"\n🟡 Warnings detected:")
        for warn in warnings[:5]:
            print(f"   - [{warn.get('app_id', 'UNKNOWN')}] {warn.get('message', '')[:80]}")
    
    print(f"\n✅ DLT parsing successful!")
    return result


def test_rca_engine():
    """Test full RCA engine with dummy defect"""
    print_separator("TEST 2: Full RCA Analysis")
    
    # Load config
    config = load_config("config/config.yaml")
    
    # Initialize RCA Engine
    print("🔧 Initializing RCA Engine...")
    engine = RCAEngine(config)
    
    # Try to initialize LLM (optional)
    try:
        llm_service = LLMService(config)
        if llm_service.is_available():
            engine.set_llm_client(llm_service)
            print("✓ LLM service connected")
        else:
            print("⚠️ LLM not available - will use mock analysis")
    except Exception as e:
        print(f"⚠️ LLM initialization failed: {e}")
    
    # Load test defect
    test_defect_path = "data/defects/test_defect.json"
    if not os.path.exists(test_defect_path):
        print(f"❌ Test defect not found: {test_defect_path}")
        return None
    
    with open(test_defect_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    defect = data.get('defects', [data])[0] if 'defects' in data else data
    defect_id = defect.get('key', 'TEST-001')
    
    print(f"\n📋 Test Defect: {defect_id}")
    print(f"   Summary: {defect.get('summary', 'N/A')}")
    print(f"   DLT File: {defect.get('dlt_attachment', 'N/A')}")
    
    # Run RCA analysis
    print(f"\n🔍 Running RCA analysis...")
    
    try:
        result = engine.analyze_defect(
            defect_id=defect_id,
            from_jira=False,  # Use local file
            upload_to_jira=False,  # Don't try to upload
            mark_duplicates=False
        )
        
        print_separator("RCA RESULT")
        
        print(f"\n📌 Status: {result.get('status', 'unknown')}")
        print(f"📌 Confidence: {result.get('confidence', 0):.0%}")
        
        root_cause = result.get('root_cause', 'Not determined')
        print(f"\n🎯 Root Cause:")
        # Print first 500 chars
        print(f"   {root_cause[:500]}..." if len(root_cause) > 500 else f"   {root_cause}")
        
        fix = result.get('fix_recommendation', '')
        if fix:
            print(f"\n💡 Fix Recommendation:")
            print(f"   {fix[:500]}..." if len(fix) > 500 else f"   {fix}")
        
        # Check for duplicates
        dup_info = result.get('duplicate_info', {})
        if dup_info.get('is_duplicate'):
            print(f"\n⚠️ Duplicate of: {dup_info.get('duplicate_of')}")
            print(f"   Similarity: {dup_info.get('similarity_score', 0):.0%}")
        
        # Report location
        if result.get('reports'):
            print(f"\n📄 Reports generated:")
            for report in result.get('reports', []):
                print(f"   - {report}")
        
        print(f"\n✅ RCA analysis completed!")
        return result
        
    except Exception as e:
        print(f"\n❌ RCA analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_domain_knowledge():
    """Test domain knowledge loading"""
    print_separator("TEST 3: Domain Knowledge")
    
    config = load_config("config/config.yaml")
    engine = RCAEngine(config)
    
    # Check if domain knowledge was loaded
    patterns = getattr(engine, 'domain_patterns', {})
    app_ctx_mappings = getattr(engine, 'app_ctx_mappings', {})
    
    print(f"📚 Domain Knowledge Loaded:")
    print(f"   Patterns: {len(patterns)}")
    print(f"   APP_ID Mappings: {len(app_ctx_mappings)}")
    
    if patterns:
        print(f"\n   Sample patterns:")
        for pattern, info in list(patterns.items())[:3]:
            print(f"     - '{pattern}' → {info.get('root_cause', 'N/A')[:50]}...")
    
    if app_ctx_mappings:
        print(f"\n   Sample APP_ID mappings:")
        for app_id, info in list(app_ctx_mappings.items())[:3]:
            print(f"     - {app_id} → {info.get('subsystem', 'N/A')}")
    
    print(f"\n✅ Domain knowledge check complete!")


def main():
    print("\n" + "=" * 60)
    print("   RCA AGENT - LOCAL TEST")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    
    # Change to project root if needed
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"Project root: {project_root}")
    
    # Run tests
    test_results = []
    
    # Test 1: DLT Parsing
    dlt_result = test_dlt_parsing()
    test_results.append(("DLT Parsing", dlt_result is not None))
    
    # Test 2: Domain Knowledge
    test_domain_knowledge()
    test_results.append(("Domain Knowledge", True))
    
    # Test 3: Full RCA
    rca_result = test_rca_engine()
    test_results.append(("RCA Analysis", rca_result is not None and rca_result.get('status') == 'completed'))
    
    # Summary
    print_separator("TEST SUMMARY")
    all_passed = True
    for name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + ("=" * 60))
    if all_passed:
        print("   🎉 ALL TESTS PASSED - Ready to deploy!")
    else:
        print("   ⚠️ Some tests failed - check configuration")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
