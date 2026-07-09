"""
RCA Infotainment Module - Automated Root Cause Analysis for Infotainment Systems

This module provides:
- DLT log analysis
- Historical defect matching
- LLM-powered root cause analysis
- JIRA integration (comment, attachment, duplicate marking)
- Git repository integration for source code access
- HTML and Markdown report generation
"""

from .rca_engine import RCAEngine
from .dlt_analyzer import DLTAnalyzer
from .historical_matcher import HistoricalMatcher
from .report_generator import ReportGenerator
from .jira_service import JiraService
from .llm_service import LLMService
from .git_service import GitService
from .source_mapper import SourceMapper

__version__ = "1.0.0"
__all__ = [
    "RCAEngine",
    "DLTAnalyzer", 
    "HistoricalMatcher", 
    "ReportGenerator",
    "JiraService",
    "LLMService",
    "GitService",
    "SourceMapper"
]
