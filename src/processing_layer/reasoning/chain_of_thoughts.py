"""
Chain of Thoughts - Implements step-by-step reasoning
"""

from typing import Dict, Any, List
import logging
import json
from src.utils.llm_client import get_llm_client


class ChainOfThoughts:
    """Implements chain-of-thought reasoning for defect analysis"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.reasoning_steps = []
        self.llm_config = llm_config or {}
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(llm_config)
            self.logger.info("Chain of Thoughts: LLM client initialized")
        except Exception as e:
            self.logger.warning(f"Chain of Thoughts: Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
    
    def reason(
        self,
        defect_data: Dict[str, Any],
        agent_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute chain-of-thought reasoning process
        
        Args:
            defect_data: Defect information
            agent_findings: Findings from AI agents
            
        Returns:
            Reasoning results with step-by-step analysis
        """
        self.logger.info("Starting chain-of-thought reasoning")
        self.reasoning_steps = []
        
        # Step 1: Understand the problem
        step1 = self._understand_problem(defect_data)
        self.reasoning_steps.append(step1)
        
        # Step 2: Analyze evidence
        step2 = self._analyze_evidence(agent_findings)
        self.reasoning_steps.append(step2)
        
        # Step 3: Generate hypotheses
        step3 = self._generate_hypotheses(defect_data, agent_findings)
        self.reasoning_steps.append(step3)
        
        # Step 4: Test hypotheses
        step4 = self._test_hypotheses(step3["hypotheses"], agent_findings)
        self.reasoning_steps.append(step4)
        
        # Step 5: Draw conclusions
        step5 = self._draw_conclusions(step4["validated_hypotheses"])
        self.reasoning_steps.append(step5)
        
        result = {
            "reasoning_steps": self.reasoning_steps,
            "conclusion": step5["conclusion"],
            "confidence": step5["confidence"],
            "supporting_evidence": step5["evidence"]
        }
        
        self.logger.info(f"Reasoning completed with {len(self.reasoning_steps)} steps")
        
        return result
    
    def _understand_problem(self, defect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Understand the problem"""
        return {
            "step": 1,
            "name": "Understand Problem",
            "description": "Analyzing defect description and context",
            "output": {
                "problem_summary": defect_data.get("description"),
                "severity": defect_data.get("severity"),
                "environment": defect_data.get("environment")
            }
        }
    
    def _analyze_evidence(self, agent_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Analyze all available evidence"""
        evidence = []
        
        for agent_name, findings in agent_findings.get("agent_results", {}).items():
            if findings.get("findings"):
                evidence.extend(findings["findings"])
        
        return {
            "step": 2,
            "name": "Analyze Evidence",
            "description": "Examining evidence from all sources",
            "output": {
                "total_evidence_pieces": len(evidence),
                "evidence_summary": evidence[:5]  # Top 5 pieces
            }
        }
    
    def _generate_hypotheses(
        self,
        defect_data: Dict[str, Any],
        agent_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 3: Generate possible hypotheses"""
        hypotheses = []
        
        # Collect hypotheses from agents
        for agent_result in agent_findings.get("agent_results", {}).values():
            if "hypotheses" in agent_result:
                hypotheses.extend(agent_result["hypotheses"])
        
        # Add general hypotheses based on defect type
        if "crash" in defect_data.get("description", "").lower():
            hypotheses.append("Application may have unhandled exception")
        
        if "slow" in defect_data.get("description", "").lower():
            hypotheses.append("Performance degradation due to resource contention")
        
        return {
            "step": 3,
            "name": "Generate Hypotheses",
            "description": "Formulating possible root causes",
            "hypotheses": hypotheses,
            "output": {
                "hypothesis_count": len(hypotheses),
                "top_hypotheses": hypotheses[:3]
            }
        }
    
    def _test_hypotheses(
        self,
        hypotheses: List[str],
        agent_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 4: Test each hypothesis against evidence"""
        validated = []
        
        for hypothesis in hypotheses:
            # Simple validation - check if evidence supports hypothesis
            support_score = self._calculate_support(hypothesis, agent_findings)
            
            validated.append({
                "hypothesis": hypothesis,
                "support_score": support_score,
                "status": "supported" if support_score > 0.5 else "not_supported"
            })
        
        # Sort by support score
        validated = sorted(validated, key=lambda x: x["support_score"], reverse=True)
        
        return {
            "step": 4,
            "name": "Test Hypotheses",
            "description": "Validating hypotheses against evidence",
            "validated_hypotheses": validated,
            "output": {
                "tested_count": len(validated),
                "supported_count": sum(1 for h in validated if h["status"] == "supported")
            }
        }
    
    def _calculate_support(
        self,
        hypothesis: str,
        agent_findings: Dict[str, Any]
    ) -> float:
        """Calculate how well evidence supports a hypothesis"""
        # Simplified support calculation
        # In production, use more sophisticated matching
        return 0.7  # Placeholder
    
    def _draw_conclusions(
        self,
        validated_hypotheses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Step 5: Draw final conclusions using LLM"""
        if not validated_hypotheses:
            return {
                "step": 5,
                "name": "Draw Conclusions",
                "description": "Formulating final diagnosis",
                "conclusion": "Unable to determine root cause",
                "confidence": 0.0,
                "evidence": []
            }
        
        # Use LLM to synthesize conclusions if available
        if self.llm_client:
            try:
                hypotheses_summary = []
                for h in validated_hypotheses[:5]:
                    hypotheses_summary.append({
                        "hypothesis": h.get('hypothesis', ''),
                        "support_score": h.get('support_score', 0)
                    })
                
                prompt = f"""Based on the validated hypotheses below, provide a comprehensive root cause analysis conclusion:

Validated Hypotheses:
{json.dumps(hypotheses_summary, indent=2)}

Provide a JSON response:
{{
    "root_cause": "The primary root cause of the defect",
    "confidence": 0.85,
    "reasoning": "Detailed explanation of why this is the root cause",
    "contributing_factors": ["factor 1", "factor 2"],
    "recommended_fix": "Specific steps to fix the issue",
    "prevention_measures": ["measure 1", "measure 2"]
}}"""
                
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message="You are an expert in software debugging and root cause analysis. Synthesize findings into a clear, actionable conclusion.",
                    temperature=0.4
                )
                
                try:
                    conclusion_data = json.loads(response)
                    return {
                        "step": 5,
                        "name": "Draw Conclusions",
                        "description": "Formulating final diagnosis",
                        "conclusion": conclusion_data.get('root_cause', 'Unknown'),
                        "confidence": conclusion_data.get('confidence', 0.5),
                        "reasoning": conclusion_data.get('reasoning', ''),
                        "contributing_factors": conclusion_data.get('contributing_factors', []),
                        "recommended_fix": conclusion_data.get('recommended_fix', ''),
                        "prevention_measures": conclusion_data.get('prevention_measures', []),
                        "evidence": [h["hypothesis"] for h in validated_hypotheses[:3]]
                    }
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse LLM response for conclusions")
                    
            except Exception as e:
                self.logger.error(f"Error drawing conclusions with LLM: {str(e)}")
        
        # Fallback: Select most supported hypothesis
        best_hypothesis = validated_hypotheses[0]
        
        return {
            "step": 5,
            "name": "Draw Conclusions",
            "description": "Formulating final diagnosis",
            "conclusion": best_hypothesis["hypothesis"],
            "confidence": best_hypothesis["support_score"],
            "evidence": [h["hypothesis"] for h in validated_hypotheses[:3]]
        }
    
    def get_reasoning_trace(self) -> List[Dict[str, Any]]:
        """Get the complete reasoning trace"""
        return self.reasoning_steps
