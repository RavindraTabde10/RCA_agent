"""
Best Practices - Stores and retrieves best practices
"""

from typing import Dict, Any, List
import logging


class BestPractices:
    """Manages best practices for defect resolution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.practices = self._load_practices()
    
    def _load_practices(self) -> List[Dict[str, Any]]:
        """Load best practices"""
        # Default best practices
        return [
            {
                "id": "BP001",
                "category": "debugging",
                "title": "Check Logs First",
                "description": "Always examine application logs before making assumptions",
                "applicability": ["all"],
                "priority": "high"
            },
            {
                "id": "BP002",
                "category": "analysis",
                "title": "Reproduce Consistently",
                "description": "Ensure defect can be reproduced consistently before analyzing",
                "applicability": ["all"],
                "priority": "high"
            },
            {
                "id": "BP003",
                "category": "resolution",
                "title": "Test Fix Thoroughly",
                "description": "Verify fix doesn't introduce new issues",
                "applicability": ["all"],
                "priority": "high"
            },
            {
                "id": "BP004",
                "category": "memory",
                "title": "Monitor Memory Usage",
                "description": "For memory-related issues, use profiling tools",
                "applicability": ["memory_leak", "out_of_memory"],
                "priority": "medium"
            },
            {
                "id": "BP005",
                "category": "performance",
                "title": "Profile Performance Bottlenecks",
                "description": "Use performance profilers to identify slow operations",
                "applicability": ["performance", "slow_response"],
                "priority": "medium"
            }
        ]
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all best practices"""
        return self.practices
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get practices by category"""
        return [
            p for p in self.practices
            if p.get("category") == category
        ]
    
    def get_applicable(
        self,
        defect_type: str,
        pattern_id: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get best practices applicable to a specific defect type
        
        Args:
            defect_type: Type of defect
            pattern_id: Optional pattern identifier
            
        Returns:
            Applicable best practices
        """
        applicable = []
        
        for practice in self.practices:
            applicability = practice.get("applicability", [])
            
            if "all" in applicability or defect_type in applicability:
                applicable.append(practice)
            elif pattern_id and pattern_id in applicability:
                applicable.append(practice)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        applicable.sort(
            key=lambda x: priority_order.get(x.get("priority", "low"), 3)
        )
        
        return applicable
    
    def add_practice(self, practice: Dict[str, Any]) -> bool:
        """
        Add a new best practice
        
        Args:
            practice: Best practice information
            
        Returns:
            Success status
        """
        required_fields = ["id", "category", "title", "description"]
        
        # Validate
        for field in required_fields:
            if field not in practice:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        self.practices.append(practice)
        self.logger.info(f"Added best practice: {practice['id']}")
        return True
    
    def get_recommendations(
        self,
        defect_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get recommended practices for a specific defect
        
        Args:
            defect_context: Defect context information
            
        Returns:
            Recommended practices
        """
        defect_type = defect_context.get("type", "unknown")
        pattern_id = defect_context.get("pattern_id")
        severity = defect_context.get("severity", "medium")
        
        # Get applicable practices
        recommendations = self.get_applicable(defect_type, pattern_id)
        
        # Add severity-based recommendations
        if severity in ["critical", "high"]:
            recommendations.extend(
                self.get_by_category("resolution")
            )
        
        # Remove duplicates
        seen_ids = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec["id"] not in seen_ids:
                seen_ids.add(rec["id"])
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]  # Top 5 recommendations
