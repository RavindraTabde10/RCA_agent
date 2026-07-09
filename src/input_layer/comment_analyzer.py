"""
Comment Analyzer - Analyzes user comments and feedback
"""

from typing import List, Dict, Any
import logging


class CommentAnalyzer:
    """Analyze and extract insights from defect comments"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze comments for insights and context
        
        Args:
            comments: List of comment objects
            
        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing {len(comments)} comments")
        
        analysis = {
            "total_comments": len(comments),
            "key_insights": [],
            "user_feedback": [],
            "workarounds": [],
            "related_issues": [],
            "sentiment": "neutral",
            "urgency_indicators": []
        }
        
        for comment in comments:
            # Extract key information
            text = comment.get("text", "")
            author = comment.get("author", "unknown")
            
            # Identify workarounds
            if self._is_workaround(text):
                analysis["workarounds"].append({
                    "author": author,
                    "text": text,
                    "timestamp": comment.get("timestamp")
                })
            
            # Identify related issues
            related = self._extract_related_issues(text)
            if related:
                analysis["related_issues"].extend(related)
            
            # Check for urgency indicators
            if self._has_urgency(text):
                analysis["urgency_indicators"].append({
                    "author": author,
                    "indicator": text
                })
        
        # Analyze overall sentiment
        analysis["sentiment"] = self._analyze_sentiment(comments)
        
        return analysis
    
    def _is_workaround(self, text: str) -> bool:
        """Check if comment contains a workaround"""
        workaround_keywords = [
            "workaround", "temporary fix", "can avoid by",
            "if you do", "try this instead"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in workaround_keywords)
    
    def _extract_related_issues(self, text: str) -> List[str]:
        """Extract references to related issues"""
        import re
        # Pattern to match common issue IDs (e.g., BUG-123, ISSUE-456)
        pattern = r'\b[A-Z]+-\d+\b'
        return re.findall(pattern, text)
    
    def _has_urgency(self, text: str) -> bool:
        """Check if comment indicates urgency"""
        urgency_keywords = [
            "urgent", "critical", "production down",
            "blocking", "asap", "immediately"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in urgency_keywords)
    
    def _analyze_sentiment(self, comments: List[Dict[str, Any]]) -> str:
        """Analyze overall sentiment of comments"""
        # Placeholder for sentiment analysis
        # In production, use NLP models for sentiment
        return "neutral"
    
    def extract_reproduction_steps(self, comments: List[Dict[str, Any]]) -> List[str]:
        """Extract reproduction steps from comments"""
        steps = []
        for comment in comments:
            text = comment.get("text", "")
            # Look for numbered lists or step indicators
            if any(indicator in text.lower() for indicator in ["step", "reproduce", "how to"]):
                steps.append(text)
        return steps
