"""
Diagnosis Generator - Generates comprehensive diagnosis reports
"""

from typing import Dict, Any, List
from datetime import datetime
import logging


class DiagnosisGenerator:
    """Generates diagnosis reports from analysis results"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate diagnosis from analysis results
        
        Args:
            analysis_results: Results from AI agent analysis
            
        Returns:
            Complete diagnosis report
        """
        self.logger.info("Generating diagnosis")
        
        diagnosis = {
            "defect_id": analysis_results.get("defect_id"),
            "timestamp": datetime.now().isoformat(),
            "root_cause": self._determine_root_cause(analysis_results),
            "confidence": self._calculate_overall_confidence(analysis_results),
            "impact": self._assess_impact(analysis_results),
            "evidence": self._compile_evidence(analysis_results),
            "recommendations": self._generate_recommendations(analysis_results),
            "assigned_team": self._suggest_team(analysis_results),
            "priority": self._determine_priority(analysis_results),
            "estimated_effort": self._estimate_effort(analysis_results),
            "related_defects": self._find_related_defects(analysis_results),
            "summary": ""
        }
        
        # Generate summary
        diagnosis["summary"] = self._generate_summary(diagnosis)
        
        self.logger.info(f"Diagnosis generated with confidence: {diagnosis['confidence']:.2%}")
        
        return diagnosis
    
    def _determine_root_cause(self, results: Dict[str, Any]) -> str:
        """Determine the root cause from analysis results"""
        # Check if chain of thoughts provided a conclusion
        if "reasoning" in results and results["reasoning"].get("conclusion"):
            return results["reasoning"]["conclusion"]
        
        # Otherwise, aggregate findings from agents
        all_findings = []
        
        for agent_result in results.get("agent_results", {}).values():
            if "findings" in agent_result:
                all_findings.extend(agent_result["findings"])
        
        if all_findings:
            # Return the most confident finding
            sorted_findings = sorted(
                all_findings,
                key=lambda x: x.get("confidence", 0),
                reverse=True
            )
            return sorted_findings[0].get("description", "Unknown root cause")
        
        return "Unable to determine root cause with available information"
    
    def _calculate_overall_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        confidence_scores = results.get("confidence_scores", {})
        
        if "overall" in confidence_scores:
            return confidence_scores["overall"]
        
        # Calculate from agent results
        if confidence_scores:
            return sum(confidence_scores.values()) / len(confidence_scores)
        
        return 0.0
    
    def _assess_impact(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact of the defect"""
        return {
            "severity": "medium",  # Placeholder
            "affected_users": "unknown",
            "affected_components": [],
            "business_impact": "moderate"
        }
    
    def _compile_evidence(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compile all evidence supporting the diagnosis"""
        evidence = []
        
        # Collect evidence from all agents
        for agent_name, agent_result in results.get("agent_results", {}).items():
            if "evidence" in agent_result:
                evidence.append({
                    "source": agent_name,
                    "evidence": agent_result["evidence"]
                })
            
            if "findings" in agent_result:
                for finding in agent_result["findings"]:
                    if "evidence" in finding:
                        evidence.append({
                            "source": agent_name,
                            "evidence": finding["evidence"]
                        })
        
        return evidence
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Collect recommendations from agents
        for agent_result in results.get("agent_results", {}).values():
            if "recommendations" in agent_result:
                recommendations.extend(agent_result["recommendations"])
        
        # Add general recommendations
        recommendations.append("Review the evidence and proposed root cause")
        recommendations.append("Test the fix in a non-production environment first")
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _suggest_team(self, results: Dict[str, Any]) -> str:
        """Suggest which team should handle the defect"""
        # Placeholder for team assignment logic
        # In production, use more sophisticated team matching
        return "Engineering Team"
    
    def _determine_priority(self, results: Dict[str, Any]) -> str:
        """Determine priority level"""
        confidence = self._calculate_overall_confidence(results)
        
        if confidence > 0.8:
            return "high"
        elif confidence > 0.5:
            return "medium"
        else:
            return "low"
    
    def _estimate_effort(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate effort required to fix"""
        return {
            "estimated_hours": "unknown",
            "complexity": "medium",
            "risk_level": "medium"
        }
    
    def _find_related_defects(self, results: Dict[str, Any]) -> List[str]:
        """Find related defects"""
        related = []
        
        # Check if pattern agent found similar defects
        for agent_result in results.get("agent_results", {}).values():
            if "similar_defects" in agent_result:
                related.extend([
                    d.get("id") for d in agent_result["similar_defects"]
                    if d.get("id")
                ])
        
        return list(set(related))
    
    def _generate_summary(self, diagnosis: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        summary_parts = []
        
        summary_parts.append(
            f"Root Cause: {diagnosis['root_cause']}"
        )
        
        summary_parts.append(
            f"Confidence Level: {diagnosis['confidence']:.0%}"
        )
        
        if diagnosis.get("assigned_team"):
            summary_parts.append(
                f"Recommended Team: {diagnosis['assigned_team']}"
            )
        
        if diagnosis.get("recommendations"):
            summary_parts.append(
                f"Key Recommendations: {'; '.join(diagnosis['recommendations'][:2])}"
            )
        
        return " | ".join(summary_parts)
    
    def format_report(
        self,
        diagnosis: Dict[str, Any],
        format_type: str = "text"
    ) -> str:
        """
        Format diagnosis as a report
        
        Args:
            diagnosis: Diagnosis information
            format_type: Output format (text, markdown, html, json)
            
        Returns:
            Formatted report
        """
        if format_type == "markdown":
            return self._format_markdown(diagnosis)
        elif format_type == "html":
            return self._format_html(diagnosis)
        elif format_type == "json":
            import json
            return json.dumps(diagnosis, indent=2)
        else:
            return self._format_text(diagnosis)
    
    def _format_text(self, diagnosis: Dict[str, Any]) -> str:
        """Format as plain text"""
        lines = []
        lines.append("=" * 60)
        lines.append("ROOT CAUSE ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"Defect ID: {diagnosis.get('defect_id')}")
        lines.append(f"Timestamp: {diagnosis.get('timestamp')}")
        lines.append(f"Priority: {diagnosis.get('priority', 'N/A').upper()}")
        lines.append("")
        lines.append("ROOT CAUSE:")
        lines.append(f"  {diagnosis.get('root_cause')}")
        lines.append(f"  Confidence: {diagnosis.get('confidence', 0):.1%}")
        lines.append("")
        lines.append("RECOMMENDATIONS:")
        for i, rec in enumerate(diagnosis.get('recommendations', []), 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")
        lines.append(f"ASSIGNED TEAM: {diagnosis.get('assigned_team', 'N/A')}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _format_markdown(self, diagnosis: Dict[str, Any]) -> str:
        """Format as Markdown"""
        lines = []
        lines.append("# Root Cause Analysis Report")
        lines.append("")
        lines.append(f"**Defect ID:** {diagnosis.get('defect_id')}")
        lines.append(f"**Timestamp:** {diagnosis.get('timestamp')}")
        lines.append(f"**Priority:** {diagnosis.get('priority', 'N/A').upper()}")
        lines.append("")
        lines.append("## Root Cause")
        lines.append(f"{diagnosis.get('root_cause')}")
        lines.append(f"- **Confidence:** {diagnosis.get('confidence', 0):.1%}")
        lines.append("")
        lines.append("## Recommendations")
        for i, rec in enumerate(diagnosis.get('recommendations', []), 1):
            lines.append(f"{i}. {rec}")
        lines.append("")
        lines.append(f"**Assigned Team:** {diagnosis.get('assigned_team', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_html(self, diagnosis: Dict[str, Any]) -> str:
        """Format as HTML"""
        # Simplified HTML output
        return f"<html><body><h1>RCA Report for {diagnosis.get('defect_id')}</h1></body></html>"
