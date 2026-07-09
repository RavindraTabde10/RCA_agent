"""
Historical Defects - Manages historical defect data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging


class HistoricalDefects:
    """Manages historical defect data for pattern analysis"""
    
    def __init__(self, storage_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path
        self.defects = self._load_defects()
    
    def _load_defects(self) -> List[Dict[str, Any]]:
        """Load historical defects from storage"""
        # Placeholder - in production, load from database
        return []
    
    def add_defect(self, defect: Dict[str, Any]) -> bool:
        """
        Add a defect to historical data
        
        Args:
            defect: Defect information
            
        Returns:
            Success status
        """
        defect["added_timestamp"] = datetime.now().isoformat()
        self.defects.append(defect)
        self.logger.info(f"Added defect to history: {defect.get('id')}")
        return True
    
    def get_defect(self, defect_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific defect by ID"""
        for defect in self.defects:
            if defect.get("id") == defect_id:
                return defect
        return None
    
    def search(
        self,
        criteria: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search historical defects
        
        Args:
            criteria: Search criteria
            limit: Maximum results
            
        Returns:
            Matching defects
        """
        results = []
        
        for defect in self.defects:
            if self._matches_criteria(defect, criteria):
                results.append(defect)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _matches_criteria(
        self,
        defect: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> bool:
        """Check if defect matches search criteria"""
        for key, value in criteria.items():
            if key not in defect or defect[key] != value:
                return False
        return True
    
    def get_by_pattern(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Get all defects matching a specific pattern"""
        return [
            d for d in self.defects
            if d.get("pattern_id") == pattern_id
        ]
    
    def get_similar_defects(
        self,
        defect_description: str,
        similarity_threshold: float = 0.7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar defects using semantic similarity
        
        Args:
            defect_description: Description to match
            similarity_threshold: Minimum similarity score
            limit: Maximum results
            
        Returns:
            Similar defects with similarity scores
        """
        # Placeholder for semantic similarity
        # In production, use embeddings and vector similarity
        similar = []
        
        return similar[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about historical defects"""
        total = len(self.defects)
        
        if total == 0:
            return {"total": 0}
        
        # Calculate statistics
        by_severity = {}
        by_component = {}
        by_pattern = {}
        
        for defect in self.defects:
            # Count by severity
            severity = defect.get("severity", "unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by component
            component = defect.get("component", "unknown")
            by_component[component] = by_component.get(component, 0) + 1
            
            # Count by pattern
            pattern = defect.get("pattern_id", "unknown")
            by_pattern[pattern] = by_pattern.get(pattern, 0) + 1
        
        return {
            "total": total,
            "by_severity": by_severity,
            "by_component": by_component,
            "by_pattern": by_pattern
        }
    
    def get_resolution_success_rate(self, pattern_id: str = None) -> float:
        """
        Calculate resolution success rate
        
        Args:
            pattern_id: Optional pattern to filter by
            
        Returns:
            Success rate (0-1)
        """
        defects_to_check = self.defects
        
        if pattern_id:
            defects_to_check = self.get_by_pattern(pattern_id)
        
        if not defects_to_check:
            return 0.0
        
        resolved = sum(
            1 for d in defects_to_check
            if d.get("status") == "resolved"
        )
        
        return resolved / len(defects_to_check)
    
    def export(self, format: str = "json") -> Any:
        """Export historical data"""
        if format == "json":
            import json
            return json.dumps(self.defects, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
