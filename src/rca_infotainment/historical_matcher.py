"""
Historical Matcher - Search and match similar historical defects

Features:
- Weighted similarity scoring (keyword-based)
- Semantic search via LanceDB vector store
- Component matching
- DLT pattern matching
- Summary/description matching
- Duplicate detection
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher


class HistoricalMatcher:
    """
    Searches and matches current defects against historical defects
    
    Supports two search modes:
    1. Keyword-based: Weighted scoring across multiple dimensions
    2. Semantic: Vector similarity using LanceDB (if available)
    
    Keyword scoring weights:
    - Component match (30%)
    - Summary similarity (25%)
    - Labels/tags match (20%)
    - DLT pattern match (15%)
    - File path match (10%)
    """
    
    # Weights for similarity calculation
    WEIGHTS = {
        "component": 0.30,
        "summary": 0.25,
        "labels": 0.20,
        "dlt_patterns": 0.15,
        "files": 0.10
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Historical Matcher
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Paths
        self.historical_path = config.get('paths', {}).get(
            'historical_defects', 
            'data/historical_defects/defects_data.json'
        )
        
        # Thresholds
        thresholds = config.get('thresholds', {})
        self.duplicate_threshold = thresholds.get('duplicate', 0.90)
        self.related_threshold = thresholds.get('related', 0.75)
        self.min_threshold = thresholds.get('min_similarity', 0.50)
        
        # Cache historical defects
        self._historical_cache = None
        
        # Vector store for semantic search (optional)
        self._vector_store = None
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize vector store if available"""
        try:
            from src.knowledge_layer.vector_store import VectorStore
            db_path = self.config.get('paths', {}).get('vector_db', 'data/vector_db')
            
            if os.path.exists(db_path):
                self._vector_store = VectorStore(db_path=db_path, llm_config=self.config.get('llm', {}))
                self.logger.info("Vector store initialized for semantic search")
            else:
                self.logger.info("Vector DB not found, using keyword-based search only")
        except ImportError:
            self.logger.info("Vector store module not available, using keyword-based search")
        except Exception as e:
            self.logger.warning(f"Failed to initialize vector store: {e}")
    
    def load_historical(self) -> List[Dict[str, Any]]:
        """Load historical defects from file"""
        if self._historical_cache is not None:
            return self._historical_cache
        
        if os.path.exists(self.historical_path):
            try:
                with open(self.historical_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both array format and {defects: [...]} format
                    if isinstance(data, list):
                        self._historical_cache = data
                    else:
                        self._historical_cache = data.get('defects', [])
                    self.logger.info(f"Loaded {len(self._historical_cache)} historical defects")
                    return self._historical_cache
            except Exception as e:
                self.logger.error(f"Error loading historical defects: {e}")
        
        self._historical_cache = []
        return self._historical_cache
    
    def search(
        self, 
        defect_data: Dict[str, Any],
        dlt_analysis: Dict[str, Any] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar historical defects
        
        Args:
            defect_data: Current defect information
            dlt_analysis: Optional DLT analysis results
            max_results: Maximum number of results to return
            
        Returns:
            List of matching historical defects with similarity scores
        """
        historical = self.load_historical()
        
        if not historical:
            self.logger.warning("No historical defects available")
            return []
        
        matches = []
        
        for hist_defect in historical:
            similarity = self._calculate_similarity(defect_data, hist_defect, dlt_analysis)
            
            if similarity >= self.min_threshold:
                matches.append({
                    "defect_id": hist_defect.get("key", hist_defect.get("id")),
                    "summary": hist_defect.get("summary", ""),
                    "component": hist_defect.get("component", "Unknown"),
                    "root_cause": hist_defect.get("root_cause", ""),
                    "resolution": hist_defect.get("resolution", ""),
                    "similarity_score": similarity,
                    "is_duplicate": similarity >= self.duplicate_threshold,
                    "is_related": similarity >= self.related_threshold,
                    "match_details": self._get_match_details(defect_data, hist_defect)
                })
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return matches[:max_results]
    
    def _calculate_similarity(
        self,
        current: Dict[str, Any],
        historical: Dict[str, Any],
        dlt_analysis: Dict[str, Any] = None
    ) -> float:
        """Calculate weighted similarity score"""
        scores = {}
        
        # Component match (exact match = 1.0, partial = 0.5)
        curr_comp = current.get("component", "").lower()
        hist_comp = historical.get("component", "").lower()
        if curr_comp and hist_comp:
            if curr_comp == hist_comp:
                scores["component"] = 1.0
            elif curr_comp in hist_comp or hist_comp in curr_comp:
                scores["component"] = 0.5
            else:
                scores["component"] = 0.0
        else:
            scores["component"] = 0.0
        
        # Summary similarity (using SequenceMatcher)
        curr_summary = current.get("summary", "").lower()
        hist_summary = historical.get("summary", "").lower()
        scores["summary"] = SequenceMatcher(None, curr_summary, hist_summary).ratio()
        
        # Labels/tags match
        curr_labels = set(current.get("labels", []))
        hist_labels = set(historical.get("labels", []))
        if curr_labels and hist_labels:
            intersection = curr_labels & hist_labels
            union = curr_labels | hist_labels
            scores["labels"] = len(intersection) / len(union) if union else 0.0
        else:
            scores["labels"] = 0.0
        
        # DLT pattern match
        if dlt_analysis:
            curr_patterns = set(p.get("type") for p in dlt_analysis.get("patterns", []))
            hist_patterns = set(historical.get("dlt_patterns", []))
            if curr_patterns and hist_patterns:
                intersection = curr_patterns & hist_patterns
                union = curr_patterns | hist_patterns
                scores["dlt_patterns"] = len(intersection) / len(union) if union else 0.0
            else:
                scores["dlt_patterns"] = 0.0
        else:
            scores["dlt_patterns"] = 0.0
        
        # File match
        curr_files = set(current.get("affected_files", []))
        hist_files = set(historical.get("affected_files", []))
        if curr_files and hist_files:
            intersection = curr_files & hist_files
            union = curr_files | hist_files
            scores["files"] = len(intersection) / len(union) if union else 0.0
        else:
            scores["files"] = 0.0
        
        # Calculate weighted total
        total = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS.keys())
        
        return round(total, 3)
    
    def _get_match_details(
        self, 
        current: Dict[str, Any], 
        historical: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get detailed breakdown of what matched"""
        details = {
            "component_match": current.get("component") == historical.get("component"),
            "matching_labels": list(
                set(current.get("labels", [])) & set(historical.get("labels", []))
            ),
            "matching_files": list(
                set(current.get("affected_files", [])) & set(historical.get("affected_files", []))
            )
        }
        return details
    
    def search_by_text(
        self, 
        query: str, 
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search historical defects by text query
        
        Args:
            query: Search query string
            max_results: Maximum results to return
            
        Returns:
            List of matching defects
        """
        historical = self.load_historical()
        query_lower = query.lower()
        
        matches = []
        
        for defect in historical:
            # Search in summary, description, root_cause
            searchable_text = " ".join([
                defect.get("summary", ""),
                defect.get("description", ""),
                defect.get("root_cause", ""),
                " ".join(defect.get("labels", []))
            ]).lower()
            
            if query_lower in searchable_text:
                # Calculate relevance
                relevance = searchable_text.count(query_lower) / len(searchable_text.split())
                
                matches.append({
                    "defect_id": defect.get("key", defect.get("id")),
                    "summary": defect.get("summary", ""),
                    "component": defect.get("component", "Unknown"),
                    "root_cause": defect.get("root_cause", ""),
                    "relevance": round(min(relevance * 10, 1.0), 2)
                })
        
        # Sort by relevance
        matches.sort(key=lambda x: x["relevance"], reverse=True)
        
        return matches[:max_results]
    
    def get_by_component(
        self, 
        component: str, 
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get historical defects by component"""
        historical = self.load_historical()
        
        matches = [
            {
                "defect_id": d.get("key", d.get("id")),
                "summary": d.get("summary", ""),
                "root_cause": d.get("root_cause", ""),
                "resolution": d.get("resolution", "")
            }
            for d in historical
            if d.get("component", "").lower() == component.lower()
        ]
        
        return matches[:max_results]
    
    def check_duplicate(
        self, 
        defect_data: Dict[str, Any],
        dlt_analysis: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if defect is a duplicate
        
        Returns:
            Duplicate info if found, None otherwise
        """
        matches = self.search(defect_data, dlt_analysis, max_results=1)
        
        if matches and matches[0]["is_duplicate"]:
            return {
                "is_duplicate": True,
                "duplicate_of": matches[0]["defect_id"],
                "similarity_score": matches[0]["similarity_score"],
                "original_root_cause": matches[0].get("root_cause"),
                "original_resolution": matches[0].get("resolution")
            }
        
        return None
    
    def semantic_search(
        self,
        query: str,
        component_filter: str = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar defects using semantic/vector similarity
        
        Uses the LanceDB vector store for AI-powered semantic matching.
        Falls back to keyword search if vector store is not available.
        
        Args:
            query: Search query (defect description, symptoms, etc.)
            component_filter: Optional component to filter by
            max_results: Maximum results to return
            
        Returns:
            List of similar defects with similarity scores
        """
        # Try semantic search first
        if self._vector_store:
            try:
                results = self._vector_store.search_similar_defects(
                    query=query,
                    limit=max_results,
                    component_filter=component_filter
                )
                
                if results:
                    # Convert vector store results to standard format
                    matches = []
                    for defect in results:
                        # Convert distance to similarity score (lower distance = higher similarity)
                        distance = defect.get('distance', 1.0)
                        similarity = max(0, 1 - distance)  # Convert distance to similarity
                        
                        matches.append({
                            "defect_id": defect.get("key"),
                            "summary": defect.get("summary", ""),
                            "component": defect.get("component", "Unknown"),
                            "root_cause": defect.get("root_cause", ""),
                            "resolution": defect.get("resolution", ""),
                            "related_file": defect.get("related_file", ""),
                            "fix_commit": defect.get("fix_commit", ""),
                            "duplicate_to": defect.get("duplicate_to", []),
                            "labels": defect.get("labels", []),
                            "similarity_score": round(similarity, 3),
                            "distance": distance,
                            "search_type": "semantic"
                        })
                    
                    self.logger.info(f"Semantic search found {len(matches)} results")
                    return matches
                    
            except Exception as e:
                self.logger.warning(f"Semantic search failed, falling back to keyword: {e}")
        
        # Fallback to keyword search
        self.logger.info("Using keyword-based search (vector store not available)")
        results = self.search_by_text(query, max_results)
        for r in results:
            r["search_type"] = "keyword"
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about historical defects"""
        historical = self.load_historical()
        
        stats = {
            "total_defects": len(historical),
            "by_component": {},
            "by_status": {},
            "with_root_cause": 0,
            "with_fix_commit": 0,
            "vector_store_available": self._vector_store is not None
        }
        
        for defect in historical:
            # Count by component
            comp = defect.get("component", "Unknown")
            stats["by_component"][comp] = stats["by_component"].get(comp, 0) + 1
            
            # Count by status
            status = defect.get("status", "Unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count with root cause
            if defect.get("root_cause"):
                stats["with_root_cause"] += 1
            
            # Count with fix commit
            if defect.get("fix_commit"):
                stats["with_fix_commit"] += 1
        
        return stats
