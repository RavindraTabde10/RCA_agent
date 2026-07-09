"""
Knowledge Base - Stores and retrieves domain knowledge
"""

from typing import Dict, Any, List, Optional
import logging


class KnowledgeBase:
    """Manages domain-specific knowledge for RCA"""
    
    def __init__(self, knowledge_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.knowledge_path = knowledge_path
        self.knowledge_store = self._load_knowledge()
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge from storage"""
        # Placeholder - in production, load from database or files
        return {
            "patterns": [],
            "solutions": [],
            "best_practices": [],
            "common_issues": []
        }
    
    def query(self, query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query the knowledge base
        
        Args:
            query: Search query
            context: Additional context for the query
            
        Returns:
            List of relevant knowledge items
        """
        self.logger.info(f"Querying knowledge base: {query}")
        
        results = []
        
        # Search in common issues
        for issue in self.knowledge_store.get("common_issues", []):
            if self._matches_query(query, issue):
                results.append(issue)
        
        # Search in solutions
        for solution in self.knowledge_store.get("solutions", []):
            if self._matches_query(query, solution):
                results.append(solution)
        
        return results
    
    def _matches_query(self, query: str, item: Dict[str, Any]) -> bool:
        """Check if an item matches the query"""
        query_lower = query.lower()
        item_text = str(item).lower()
        return query_lower in item_text
    
    def get_similar_issues(
        self,
        defect_description: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical issues
        
        Args:
            defect_description: Description of current defect
            limit: Maximum number of results
            
        Returns:
            List of similar issues
        """
        # Placeholder for similarity search
        # In production, use vector embeddings and similarity matching
        return []
    
    def get_solution_for_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get recommended solution for a known pattern"""
        solutions = self.knowledge_store.get("solutions", [])
        
        for solution in solutions:
            if solution.get("pattern_id") == pattern_id:
                return solution
        
        return None
    
    def add_knowledge(self, knowledge_item: Dict[str, Any]) -> bool:
        """
        Add new knowledge to the base
        
        Args:
            knowledge_item: Knowledge item to add
            
        Returns:
            Success status
        """
        item_type = knowledge_item.get("type")
        
        if item_type == "pattern":
            self.knowledge_store["patterns"].append(knowledge_item)
        elif item_type == "solution":
            self.knowledge_store["solutions"].append(knowledge_item)
        elif item_type == "best_practice":
            self.knowledge_store["best_practices"].append(knowledge_item)
        elif item_type == "common_issue":
            self.knowledge_store["common_issues"].append(knowledge_item)
        else:
            self.logger.warning(f"Unknown knowledge type: {item_type}")
            return False
        
        self.logger.info(f"Added knowledge item of type: {item_type}")
        return True
    
    def get_best_practices(self, category: str = None) -> List[Dict[str, Any]]:
        """Get best practices, optionally filtered by category"""
        practices = self.knowledge_store.get("best_practices", [])
        
        if category:
            practices = [p for p in practices if p.get("category") == category]
        
        return practices
    
    def update_from_resolution(self, defect_id: str, resolution: Dict[str, Any]):
        """
        Update knowledge base from defect resolution
        
        Args:
            defect_id: Defect identifier
            resolution: Resolution information
        """
        # Extract learnings from resolution
        if resolution.get("root_cause") and resolution.get("solution"):
            knowledge_item = {
                "type": "solution",
                "defect_id": defect_id,
                "root_cause": resolution["root_cause"],
                "solution": resolution["solution"],
                "effectiveness": resolution.get("effectiveness", "unknown")
            }
            
            self.add_knowledge(knowledge_item)
            self.logger.info(f"Updated knowledge base from resolution: {defect_id}")
