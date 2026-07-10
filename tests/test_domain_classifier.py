#!/usr/bin/env python3
"""
Quick test for domain classifier integration - NO JIRA interaction
"""

import warnings
warnings.filterwarnings('ignore')

import sys
import logging
logging.disable(logging.WARNING)  # Suppress warnings

sys.path.insert(0, '.')

from src.rca_infotainment.domain_classifier import DomainClassifier, predict_domain_for_defect

def test_domain_classifier():
    """Test the domain classifier with sample defects"""
    
    print("="*60)
    print("  Domain Classifier Test (No JIRA)")
    print("="*60)
    
    # Initialize classifier
    dc = DomainClassifier()
    
    if dc.is_available():
        print(f"\nClassifier: ML Model (Sentence Transformer + Logistic Regression)")
    else:
        print(f"\nClassifier: Keyword Fallback (ML model not available)")
    
    # Test cases
    test_defects = [
        {
            "summary": "Audio stutters during USB playback",
            "description": "Buffer underrun detected in audio HAL. Samples dropped."
        },
        {
            "summary": "Bluetooth phone disconnects after 10 minutes",
            "description": "HFP connection lost. Auto-reconnect fails."
        },
        {
            "summary": "System takes 90 seconds to boot",
            "description": "Kernel initialization slow. Service startup delayed."
        },
        {
            "summary": "Memory leak in navigation service",
            "description": "Memory grows 50MB per hour. OOM after 6 hours."
        }
    ]
    
    print("\n" + "-"*60)
    print("Test Results:")
    print("-"*60)
    
    for i, defect in enumerate(test_defects, 1):
        result = dc.predict_from_defect(defect)
        print(f"\n{i}. {defect['summary'][:50]}...")
        print(f"   Domain:     {result['domain_display']}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Team:       {result['team']}")
        print(f"   Method:     {result['method']}")
    
    print("\n" + "="*60)
    print("Domain Classifier Test PASSED")
    print("="*60)

if __name__ == "__main__":
    test_domain_classifier()
