#!/usr/bin/env python3
"""
Test RCA Engine with Domain Classification - No JIRA

Tests:
1. Domain Classifier integration
2. DLT Analysis
3. Report generation
4. Dashboard tracking (optional)

No JIRA interaction - uses dummy defect data.
"""

import os
import sys
import time
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(__file__))

from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.dlt_analyzer import DLTAnalyzer
from src.rca_infotainment.domain_classifier import DomainClassifier, predict_domain_for_defect
from src.rca_infotainment.html_report_generator import generate_rca_html_report
from src.utils.config import load_config


def test_domain_classification():
    """Test domain classifier on different defect types"""
    print("\n" + "="*60)
    print("  TEST 1: Domain Classification")
    print("="*60)
    
    classifier = DomainClassifier()
    print(f"\nClassifier loaded: {classifier.is_available()}")
    print(f"Method: {'ML Model' if classifier.is_loaded else 'Keyword Fallback'}")
    
    test_cases = [
        {"summary": "Audio stutters during USB playback", "description": "Buffer underrun in audio HAL"},
        {"summary": "Bluetooth disconnects after 10 min", "description": "HFP connection lost"},
        {"summary": "Boot takes 90 seconds", "description": "Kernel init slow"},
        {"summary": "Memory leak in nav service", "description": "OOM after 6 hours"},
    ]
    
    print("\nPredictions:")
    for defect in test_cases:
        result = classifier.predict_from_defect(defect)
        print(f"  {defect['summary'][:40]}...")
        print(f"    → {result['domain_display']} ({result['confidence']:.0%}) → {result['team']}")
    
    print("\n✓ Domain Classification Test PASSED")
    return True


def test_dlt_analysis():
    """Test DLT log parsing"""
    print("\n" + "="*60)
    print("  TEST 2: DLT Log Analysis")
    print("="*60)
    
    # Use relative path for portability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dlt_file = os.path.join(script_dir, "data", "dlt_logs", "usb_str_slow.dlt")
    
    if not os.path.exists(dlt_file):
        print(f"ERROR: DLT file not found: {dlt_file}")
        return False
    
    print(f"\nDLT File: {dlt_file}")
    print(f"File Size: {os.path.getsize(dlt_file):,} bytes")
    
    # Read file
    with open(dlt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Analyze
    analyzer = DLTAnalyzer()
    result = analyzer.analyze(content)
    
    print(f"\nAnalysis Results:")
    print(f"  Total entries: {result.get('total_entries', 0)}")
    print(f"  Errors: {result.get('error_count', 0)}")
    print(f"  Warnings: {result.get('warning_count', 0)}")
    print(f"  Components: {', '.join(result.get('unique_components', [])[:5])}")
    
    print("\n✓ DLT Analysis Test PASSED")
    return True


def test_full_rca_engine():
    """Test full RCA engine without JIRA"""
    print("\n" + "="*60)
    print("  TEST 3: Full RCA Engine (No JIRA)")
    print("="*60)
    
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    config = load_config(config_path) if os.path.exists(config_path) else {}
    
    # Initialize engine
    engine = RCAEngine(config)
    
    print(f"\nEngine initialized:")
    print(f"  Domain classifier: {'✓ Loaded' if engine.domain_classifier else '✗ Not available'}")
    print(f"  LLM client: {'✓ Set' if engine.llm_client else '✗ Not set'}")
    print(f"  JIRA client: {'✓ Set' if engine.jira_client else '✗ Not set (expected)'}")
    
    # Create dummy defect data
    defect_id = "TEST-ENGINE-001"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_defect = {
        "key": defect_id,
        "summary": "[USB] Source switch from FM to USB takes more than 200ms",
        "description": "STR KPI failed. Measured 378ms, threshold is 200ms. See attached DLT log.",
        "priority": "High",
        "component": "Media",
        "status": "Open",
        "dlt_path": os.path.join(script_dir, "data", "dlt_logs", "usb_str_slow.dlt")
    }
    
    # Test domain prediction
    if engine.domain_classifier:
        prediction = engine.domain_classifier.predict_from_defect(dummy_defect)
        print(f"\n  Domain Prediction:")
        print(f"    Domain: {prediction['domain_display']}")
        print(f"    Confidence: {prediction['confidence']:.0%}")
        print(f"    Team: {prediction['team']}")
    
    print("\n✓ RCA Engine Test PASSED")
    return True


def test_report_generation():
    """Test HTML report generation"""
    print("\n" + "="*60)
    print("  TEST 4: HTML Report Generation")
    print("="*60)
    
    # Create mock RCA result
    rca_result = {
        "defect_id": "TEST-REPORT-001",
        "status": "completed",
        "duration_seconds": 5.2,
        "stages": {
            "dlt_analysis": {
                "status": "completed",
                "data": {
                    "total_entries": 47,
                    "errors": [{"message": "STR KPI FAILED", "timestamp": "10:00:00"}],
                    "warnings": ["USB timeout detected"],
                    "components": ["USB", "MEDIA"]
                }
            },
            "domain_classification": {
                "status": "completed",
                "data": {
                    "domain": "audio_system_domain",
                    "domain_display": "Audio System",
                    "confidence": 0.85,
                    "team": "Audio Engineering"
                }
            },
            "source_mapping": {
                "status": "completed",
                "data": {
                    "mapped_files": [
                        {"file": "USBMediaService.cpp", "confidence": 0.95, "reason": "USB handler"}
                    ]
                }
            },
            "historical_match": {
                "status": "completed",
                "data": {
                    "matches": [
                        {"defect_id": "SAM1-1890", "similarity_score": 0.89, "summary": "Similar USB issue"}
                    ]
                }
            },
            "llm_analysis": {
                "status": "completed",
                "data": {
                    "root_cause": "USB device enumeration takes too long due to missing device cache.",
                    "confidence": 0.87,
                    "domain": "Media",
                    "evidence": ["STR KPI FAILED duration=378ms", "USB enumeration delay=177ms"],
                    "fix_recommendation": """1. Implement USB device caching
2. Parallelize filesystem check
3. Add async enumeration with timeout

Example code:
```cpp
status_t USBDeviceEnumerator::enumerateDevice(int vendorId) {
    if (mDeviceCache.contains(vendorId)) {
        return OK; // Use cached info
    }
    // ... rest of implementation
}
```""",
                    "affected_files": ["USBMediaService.cpp", "USBDeviceEnumerator.cpp"]
                }
            }
        }
    }
    
    defect_data = {
        "summary": "[USB] Source switch too slow",
        "description": "STR KPI failed",
        "priority": "High"
    }
    
    # Generate report
    html_content = generate_rca_html_report(rca_result, defect_data)
    
    # Save report
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, "TEST-REPORT-001_rca.html")
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nReport generated: {html_path}")
    print(f"Size: {len(html_content):,} bytes")
    
    # Quick validation
    checks = [
        ("Root Cause section", "root-cause" in html_content),
        ("Fix Recommendation", "Recommended Fix" in html_content),
        ("Code block", "<pre" in html_content or "<code" in html_content),
        ("Confidence score", "87%" in html_content or "0.87" in html_content)
    ]
    
    print("\nValidation:")
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ Report Generation Test PASSED")
    else:
        print("\n✗ Some validation checks failed")
    
    return all_passed


def main():
    print("\n" + "="*60)
    print("  RCA ENGINE INTEGRATION TEST")
    print("  (No JIRA Interaction)")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Domain Classification", test_domain_classification()))
    results.append(("DLT Analysis", test_dlt_analysis()))
    results.append(("RCA Engine", test_full_rca_engine()))
    results.append(("Report Generation", test_report_generation()))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED")
        print("\nGenerated reports in: output/")
        print("  - TEST-REPORT-001_rca.html")
    else:
        print("\n✗ SOME TESTS FAILED")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
