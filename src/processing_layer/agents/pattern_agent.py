"""
Pattern Agent - Specialized agent for pattern recognition
"""

from typing import Dict, Any, List
import logging
import json
from src.utils.llm_client import get_llm_client
from src.knowledge_layer.vector_store import get_vector_store


class PatternAgent:
    """AI agent specialized in recognizing defect patterns"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.llm_config = llm_config or {}
        
        # Known defect patterns
        self.known_patterns = self._load_known_patterns()
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(llm_config)
            self.logger.info("Pattern Agent: LLM client initialized")
        except Exception as e:
            self.logger.warning(f"Pattern Agent: Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
        
        # Initialize Vector Store for semantic search
        try:
            self.vector_store = get_vector_store()
            self.logger.info("Pattern Agent: Vector store initialized")
        except Exception as e:
            self.logger.warning(f"Pattern Agent: Failed to initialize vector store: {str(e)}")
            self.vector_store = None
    
    def analyze(
        self,
        defect_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze defect for known patterns
        
        Args:
            defect_data: Current defect information
            historical_data: Historical defect data
            
        Returns:
            Analysis results with pattern matches
        """
        self.logger.info("Pattern Agent: Starting pattern analysis")
        
        results = {
            "agent": "pattern_agent",
            "matched_patterns": [],
            "similar_defects": [],
            "confidence": 0.0,
            "pattern_type": "unknown",
            "recommendations": []
        }
        
        # Match against known patterns
        pattern_matches = self._match_patterns(defect_data)
        results["matched_patterns"] = pattern_matches
        
        # Find similar historical defects
        similar = self._find_similar_defects(defect_data, historical_data)
        results["similar_defects"] = similar
        
        # Determine pattern type
        results["pattern_type"] = self._determine_pattern_type(
            pattern_matches,
            similar
        )
        
        # Generate recommendations based on patterns
        results["recommendations"] = self._generate_recommendations(
            results["matched_patterns"],
            results["similar_defects"]
        )
        
        # Calculate confidence
        results["confidence"] = self._calculate_confidence(results)
        
        self.logger.info(f"Pattern Agent: Matched {len(pattern_matches)} patterns")
        
        return results
    
    def _load_known_patterns(self) -> List[Dict[str, Any]]:
        """Load known defect patterns"""
        # Placeholder for pattern database
        return [
            {
                "id": "MEMORY_LEAK",
                "name": "Memory Leak",
                "indicators": ["OutOfMemoryError", "heap space", "memory"],
                "typical_causes": ["Unclosed resources", "Static references"]
            },
            {
                "id": "NULL_POINTER",
                "name": "Null Pointer Exception",
                "indicators": ["NullPointerException", "null reference"],
                "typical_causes": ["Missing null checks", "Uninitialized variables"]
            },
            {
                "id": "RACE_CONDITION",
                "name": "Race Condition",
                "indicators": ["intermittent", "timing", "concurrent"],
                "typical_causes": ["Thread synchronization", "Shared state"]
            }
        ]
    
    def _match_patterns(self, defect_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Match defect against known patterns"""
        matches = []
        
        defect_text = (
            defect_data.get("description", "") + " " +
            defect_data.get("actual_behavior", "")
        ).lower()
        
        for pattern in self.known_patterns:
            # Check if any indicators are present
            matches_found = [
                indicator for indicator in pattern["indicators"]
                if indicator.lower() in defect_text
            ]
            
            if matches_found:
                matches.append({
                    "pattern_id": pattern["id"],
                    "pattern_name": pattern["name"],
                    "matched_indicators": matches_found,
                    "confidence": len(matches_found) / len(pattern["indicators"]),
                    "typical_causes": pattern["typical_causes"]
                })
        
        return sorted(matches, key=lambda x: x["confidence"], reverse=True)
    
    def _find_similar_defects(
        self,
        current_defect: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find similar historical defects using vector database and LLM"""
        similar = []
        
        # Primary: Use vector database for semantic search
        if self.vector_store:
            try:
                current_description = current_defect.get('description', '')
                component = current_defect.get('component', None)
                
                # Search for similar defects in vector database
                vector_results = self.vector_store.search_similar_defects(
                    query=current_description,
                    limit=10,
                    component_filter=component if component else None
                )
                
                self.logger.info(f"Vector store found {len(vector_results)} similar defects")
                
                # Convert vector results to standard format
                for result in vector_results:
                    # Distance to similarity score (lower distance = higher similarity)
                    # Normalize distance to 0-1 range (assuming max distance ~2.0)
                    similarity_score = max(0, 1 - (result.get('distance', 2.0) / 2.0))
                    
                    similar.append({
                        "defect": {
                            "key": result.get('key'),
                            "description": result.get('summary'),
                            "component": result.get('component'),
                            "root_cause": result.get('root_cause'),
                            "status": result.get('status'),
                            "resolution": result.get('resolution')
                        },
                        "similarity_score": similarity_score,
                        "distance": result.get('distance'),
                        "reasoning": f"Semantic similarity from vector database (distance: {result.get('distance', 0):.4f})"
                    })
                
                if similar:
                    self.logger.info(f"Found {len(similar)} similar defects using vector database")
                    return similar
                    
            except Exception as e:
                self.logger.error(f"Error searching vector database: {str(e)}")
        
        # Secondary: Use LLM for semantic similarity if historical data provided
        if not similar and self.llm_client and len(historical_data) > 0:
            try:
                current_description = current_defect.get('description', '')
                historical_summaries = []
                
                for idx, hist_defect in enumerate(historical_data[:10]):  # Limit to 10 for context
                    historical_summaries.append({
                        "id": idx,
                        "description": hist_defect.get('description', '')[:200],
                        "root_cause": hist_defect.get('root_cause', 'unknown')
                    })
                
                prompt = f"""Compare the current defect with historical defects and identify the most similar ones:

Current Defect:
{current_description}

Historical Defects:
{json.dumps(historical_summaries, indent=2)}

Provide a JSON response with similar defects (sorted by similarity):
{{
    "similar_defects": [
        {{
            "id": 0,
            "similarity_score": 0.85,
            "reasoning": "Why this is similar"
        }}
    ]
}}

Return only defects with similarity_score > 0.6"""
                
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message="You are an expert in identifying similar software defects and patterns.",
                    temperature=0.3
                )
                
                try:
                    analysis = json.loads(response)
                    for match in analysis.get('similar_defects', []):
                        hist_id = match.get('id')
                        if hist_id < len(historical_data):
                            similar.append({
                                "defect": historical_data[hist_id],
                                "similarity_score": match.get('similarity_score', 0),
                                "reasoning": match.get('reasoning', '')
                            })
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse LLM response for similar defects")
                    
            except Exception as e:
                self.logger.error(f"Error finding similar defects with LLM: {str(e)}")
        
        # Tertiary: simple keyword matching fallback
        if not similar and historical_data:
            self.logger.info("Using keyword matching fallback")
            current_keywords = set(current_defect.get('description', '').lower().split())
            
            for hist_defect in historical_data[:5]:
                hist_keywords = set(hist_defect.get('description', '').lower().split())
                common_keywords = current_keywords & hist_keywords
                
                if len(common_keywords) > 3:
                    similar.append({
                        "defect": hist_defect,
                        "similarity_score": len(common_keywords) / max(len(current_keywords), 1),
                        "common_keywords": list(common_keywords),
                        "reasoning": "Keyword-based similarity"
                    })
        
        return similar
    
    def _determine_pattern_type(
        self,
        pattern_matches: List[Dict[str, Any]],
        similar_defects: List[Dict[str, Any]]
    ) -> str:
        """Determine the type of pattern"""
        if pattern_matches:
            return pattern_matches[0]["pattern_name"]
        elif similar_defects:
            return "similar_to_known_issue"
        else:
            return "unknown"
    
    def _generate_recommendations(
        self,
        pattern_matches: List[Dict[str, Any]],
        similar_defects: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on patterns"""
        recommendations = []
        
        for match in pattern_matches:
            recommendations.append(
                f"Pattern detected: {match['pattern_name']}. "
                f"Typical causes: {', '.join(match['typical_causes'])}"
            )
        
        if similar_defects:
            recommendations.append(
                f"Found {len(similar_defects)} similar historical defects. "
                "Review their resolutions."
            )
        
        return recommendations
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        if results["matched_patterns"]:
            # Use highest pattern match confidence
            return max(p["confidence"] for p in results["matched_patterns"])
        elif results["similar_defects"]:
            return 0.5
        else:
            return 0.0
