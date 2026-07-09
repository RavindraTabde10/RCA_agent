"""
Test Diagnosis Generator
"""

import pytest
from src.output_layer.diagnosis_generator import DiagnosisGenerator


def test_diagnosis_generator_initialization():
    """Test that DiagnosisGenerator initializes correctly"""
    generator = DiagnosisGenerator()
    assert generator is not None


def test_generate_diagnosis():
    """Test diagnosis generation"""
    generator = DiagnosisGenerator()
    
    analysis_results = {
        "defect_id": "TEST-123",
        "agent_results": {
            "log_agent": {
                "findings": [
                    {"description": "Error found", "confidence": 0.8}
                ]
            }
        },
        "confidence_scores": {"overall": 0.75}
    }
    
    diagnosis = generator.generate(analysis_results)
    
    assert diagnosis is not None
    assert diagnosis["defect_id"] == "TEST-123"
    assert "root_cause" in diagnosis
    assert "confidence" in diagnosis
    assert "recommendations" in diagnosis


def test_format_report_text():
    """Test text report formatting"""
    generator = DiagnosisGenerator()
    
    diagnosis = {
        "defect_id": "TEST-123",
        "root_cause": "Memory leak",
        "confidence": 0.85,
        "priority": "high",
        "recommendations": ["Fix memory leak", "Add monitoring"],
        "assigned_team": "Backend"
    }
    
    report = generator.format_report(diagnosis, format_type="text")
    
    assert "ROOT CAUSE ANALYSIS REPORT" in report
    assert "TEST-123" in report
    assert "Memory leak" in report


def test_format_report_markdown():
    """Test markdown report formatting"""
    generator = DiagnosisGenerator()
    
    diagnosis = {
        "defect_id": "TEST-456",
        "root_cause": "Database timeout",
        "confidence": 0.75,
        "recommendations": ["Increase timeout", "Optimize query"]
    }
    
    report = generator.format_report(diagnosis, format_type="markdown")
    
    assert "# Root Cause Analysis Report" in report
    assert "**Defect ID:**" in report
    assert "Database timeout" in report


if __name__ == "__main__":
    pytest.main([__file__])
