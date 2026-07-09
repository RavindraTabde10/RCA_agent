"""
Hypothesis Generator - Generates and tests hypotheses
"""

from typing import Dict, Any, List
import logging
import json
from src.utils.llm_client import get_llm_client
from src.knowledge_layer.vector_store import get_vector_store


class HypothesisGenerator:
    """Generates and tests hypotheses about root causes"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.llm_config = llm_config or {}
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(llm_config)
            self.logger.info("Hypothesis Generator: LLM client initialized")
        except Exception as e:
            self.logger.warning(f"Hypothesis Generator: Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
        
        # Initialize Vector Store for historical defect search
        try:
            self.vector_store = get_vector_store()
            self.logger.info("Hypothesis Generator: Vector store initialized")
        except Exception as e:
            self.logger.warning(f"Hypothesis Generator: Failed to initialize vector store: {str(e)}")
            self.vector_store = None
    
    def generate_hypotheses(
        self,
        defect_data: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        domain_knowledge: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate hypotheses about root causes
        
        Args:
            defect_data: Defect information
            evidence: Available evidence
            domain_knowledge: Domain-specific knowledge
            
        Returns:
            List of hypotheses
        """
        self.logger.info("Generating hypotheses")
        
        hypotheses = []
        
        # Generate hypotheses from evidence
        evidence_based = self._generate_from_evidence(evidence)
        hypotheses.extend(evidence_based)
        
        # Generate hypotheses from defect description
        description_based = self._generate_from_description(defect_data)
        hypotheses.extend(description_based)
        
        # Generate hypotheses from historical defects (vector database)
        historical_based = self._generate_from_historical_defects(defect_data)
        hypotheses.extend(historical_based)
        
        # Generate hypotheses from domain knowledge
        if domain_knowledge:
            knowledge_based = self._generate_from_knowledge(
                defect_data,
                domain_knowledge
            )
            hypotheses.extend(knowledge_based)
        
        # Remove duplicates
        hypotheses = self._deduplicate(hypotheses)
        
        # Use LLM to generate additional sophisticated hypotheses
        if self.llm_client:
            llm_hypotheses = self._generate_with_llm(defect_data, evidence, domain_knowledge)
            hypotheses.extend(llm_hypotheses)
            hypotheses = self._deduplicate(hypotheses)
        
        self.logger.info(f"Generated {len(hypotheses)} hypotheses")
        
        return hypotheses
    
    def _generate_from_evidence(
        self,
        evidence: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses from evidence"""
        hypotheses = []
        
        for item in evidence:
            if item.get("type") == "error":
                hypotheses.append({
                    "hypothesis": f"Error in {item.get('component', 'system')} component",
                    "source": "evidence",
                    "confidence": 0.6,
                    "supporting_evidence": [item]
                })
            
            if item.get("type") == "exception":
                hypotheses.append({
                    "hypothesis": "Unhandled exception in application logic",
                    "source": "evidence",
                    "confidence": 0.7,
                    "supporting_evidence": [item]
                })
        
        return hypotheses
    
    def _generate_from_description(
        self,
        defect_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses from defect description"""
        hypotheses = []
        description = defect_data.get("description", "").lower()
        
        # Pattern-based hypothesis generation
        if "crash" in description or "crashes" in description:
            hypotheses.append({
                "hypothesis": "Application crash due to runtime error",
                "source": "description",
                "confidence": 0.5
            })
        
        if "slow" in description or "performance" in description:
            hypotheses.append({
                "hypothesis": "Performance degradation due to resource constraints",
                "source": "description",
                "confidence": 0.5
            })
        
        if "memory" in description:
            hypotheses.append({
                "hypothesis": "Memory-related issue (leak or exhaustion)",
                "source": "description",
                "confidence": 0.6
            })
        
        if "timeout" in description:
            hypotheses.append({
                "hypothesis": "Timeout due to long-running operation",
                "source": "description",
                "confidence": 0.5
            })
        
        return hypotheses
    
    def _generate_from_historical_defects(
        self,
        defect_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses from similar historical defects in vector database"""
        hypotheses = []
        
        if not self.vector_store:
            return hypotheses
        
        try:
            # Get defect description for search
            description = defect_data.get('description', '')
            component = defect_data.get('component', None)
            
            if not description:
                return hypotheses
            
            # Search for similar historical defects
            similar_defects = self.vector_store.search_similar_defects(
                query=description,
                limit=5,
                component_filter=component if component else None
            )
            
            self.logger.info(f"Found {len(similar_defects)} similar historical defects")
            
            # Generate hypotheses from historical root causes
            for defect in similar_defects:
                root_cause = defect.get('root_cause', '')
                distance = defect.get('distance', 2.0)
                
                # Convert distance to confidence (lower distance = higher confidence)
                # Distance typically ranges from 0-2, normalize to 0.3-0.8 confidence
                confidence = max(0.3, min(0.8, 1 - (distance / 2.0)))
                
                if root_cause and root_cause != 'unknown':
                    hypotheses.append({
                        "hypothesis": f"Similar to {defect.get('key')}: {root_cause}",
                        "source": "historical_defects",
                        "confidence": confidence,
                        "reasoning": f"Found similar defect {defect.get('key')} with distance {distance:.4f}\",
                        "supporting_evidence": [{
                            "type": "historical_defect",
                            "defect_key": defect.get('key'),
                            "summary": defect.get('summary'),
                            "component": defect.get('component'),
                            "root_cause": root_cause,
                            "similarity_distance": distance
                        }]
                    })
            
            if hypotheses:
                self.logger.info(f"Generated {len(hypotheses)} hypotheses from historical defects")
                
        except Exception as e:
            self.logger.error(f"Error generating hypotheses from historical defects: {str(e)}")
        
        return hypotheses
    
    def _generate_from_knowledge(
        self,
        defect_data: Dict[str, Any],
        domain_knowledge: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses from domain knowledge"""
        hypotheses = []
        
        # Use domain knowledge to generate informed hypotheses
        # Placeholder for knowledge-based generation
        
        return hypotheses
    
    def _deduplicate(
        self,
        hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate hypotheses"""
        seen = set()
        unique = []
        
        for h in hypotheses:
            key = h["hypothesis"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(h)
        
        return unique
    
    def _generate_with_llm(
        self,
        defect_data: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        domain_knowledge: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses using LLM"""
        hypotheses = []
        
        if not self.llm_client:
            return hypotheses
        
        try:
            # Prepare context for LLM
            defect_summary = {
                "description": defect_data.get('description', ''),
                "severity": defect_data.get('severity', 'unknown'),
                "component": defect_data.get('component', 'unknown')
            }
            
            # Summarize evidence
            evidence_summary = []
            for item in evidence[:5]:  # Limit to 5 items
                evidence_summary.append({
                    "type": item.get('type', 'unknown'),
                    "description": str(item.get('description', ''))[:200]
                })
            
            prompt = f"""As a root cause analysis expert, generate 3-5 plausible hypotheses for this software defect:

Defect Information:
{json.dumps(defect_summary, indent=2)}

Available Evidence:
{json.dumps(evidence_summary, indent=2)}

Generate hypotheses in JSON format:
{{
    "hypotheses": [
        {{
            "hypothesis": "Clear, concise hypothesis statement",
            "confidence": 0.7,
            "reasoning": "Why this hypothesis is plausible",
            "test_approach": "How to verify this hypothesis",
            "related_components": ["component1", "component2"]
        }}
    ]
}}

Focus on:
1. Root causes, not symptoms
2. Technical accuracy
3. Testable hypotheses
4. Diverse possibilities"""
            
            response = self.llm_client.analyze_text(
                prompt=prompt,
                system_message="You are an expert software engineer specializing in debugging and root cause analysis.",
                temperature=0.6
            )
            
            try:
                llm_result = json.loads(response)
                for h in llm_result.get('hypotheses', []):
                    hypotheses.append({
                        "hypothesis": h.get('hypothesis', ''),
                        "source": "llm",
                        "confidence": h.get('confidence', 0.5),
                        "reasoning": h.get('reasoning', ''),
                        "test_approach": h.get('test_approach', ''),
                        "related_components": h.get('related_components', [])
                    })
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse LLM response for hypotheses")
                
        except Exception as e:
            self.logger.error(f"Error generating hypotheses with LLM: {str(e)}")
        
        return hypotheses
    
    def test_hypothesis(
        self,
        hypothesis: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Test a hypothesis against available evidence
        
        Args:
            hypothesis: Hypothesis to test
            evidence: Available evidence
            
        Returns:
            Test results with confidence score
        """
        self.logger.debug(f"Testing hypothesis: {hypothesis['hypothesis']}")
        
        supporting = []
        contradicting = []
        
        for item in evidence:
            if self._supports_hypothesis(hypothesis, item):
                supporting.append(item)
            elif self._contradicts_hypothesis(hypothesis, item):
                contradicting.append(item)
        
        # Calculate confidence based on supporting/contradicting evidence
        total = len(supporting) + len(contradicting)
        if total == 0:
            confidence = hypothesis.get("confidence", 0.5)
        else:
            confidence = len(supporting) / total
        
        return {
            "hypothesis": hypothesis,
            "confidence": confidence,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "status": "validated" if confidence > 0.6 else "uncertain"
        }
    
    def _supports_hypothesis(
        self,
        hypothesis: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> bool:
        """Check if evidence supports hypothesis"""
        # Simplified support checking
        # In production, use semantic similarity
        return False
    
    def _contradicts_hypothesis(
        self,
        hypothesis: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> bool:
        """Check if evidence contradicts hypothesis"""
        return False
    
    def rank_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        test_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank hypotheses by confidence"""
        # Merge test results into hypotheses
        ranked = []
        
        for hypothesis in hypotheses:
            # Find corresponding test result
            test_result = next(
                (t for t in test_results if t["hypothesis"] == hypothesis),
                None
            )
            
            if test_result:
                hypothesis["final_confidence"] = test_result["confidence"]
                hypothesis["status"] = test_result["status"]
            
            ranked.append(hypothesis)
        
        # Sort by confidence
        return sorted(
            ranked,
            key=lambda x: x.get("final_confidence", x.get("confidence", 0)),
            reverse=True
        )
