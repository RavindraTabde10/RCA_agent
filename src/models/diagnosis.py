"""
Diagnosis Model - Represents an RCA diagnosis
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Diagnosis:
    """Represents a root cause analysis diagnosis"""
    
    defect_id: str
    root_cause: str
    confidence: float
    
    # Timestamp
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Analysis details
    impact: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    best_practices: List[Dict[str, Any]] = field(default_factory=list)
    
    # Assignment
    assigned_team: Optional[str] = None
    assignment_confidence: Optional[float] = None
    assignment_reasons: List[str] = field(default_factory=list)
    
    # Priority and effort
    priority: str = "medium"
    estimated_effort: Dict[str, Any] = field(default_factory=dict)
    
    # Related information
    related_defects: List[str] = field(default_factory=list)
    similar_patterns: List[str] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    
    # Agent contributions
    agent_results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "defect_id": self.defect_id,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "generated_at": self.generated_at,
            "impact": self.impact,
            "evidence": self.evidence,
            "reasoning_steps": self.reasoning_steps,
            "recommendations": self.recommendations,
            "best_practices": self.best_practices,
            "assigned_team": self.assigned_team,
            "assignment_confidence": self.assignment_confidence,
            "assignment_reasons": self.assignment_reasons,
            "priority": self.priority,
            "estimated_effort": self.estimated_effort,
            "related_defects": self.related_defects,
            "similar_patterns": self.similar_patterns,
            "summary": self.summary,
            "agent_results": self.agent_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Diagnosis':
        """Create from dictionary"""
        return cls(**data)
    
    def get_confidence_level(self) -> str:
        """Get human-readable confidence level"""
        if self.confidence >= 0.8:
            return "High"
        elif self.confidence >= 0.5:
            return "Medium"
        else:
            return "Low"
    
    def get_top_recommendations(self, count: int = 3) -> List[str]:
        """Get top N recommendations"""
        return self.recommendations[:count]
    
    def add_evidence(self, evidence_item: Dict[str, Any]):
        """Add evidence to diagnosis"""
        self.evidence.append(evidence_item)
    
    def format_summary(self) -> str:
        """Format a concise summary"""
        if self.summary:
            return self.summary
        
        parts = []
        parts.append(f"Root Cause: {self.root_cause}")
        parts.append(f"Confidence: {self.get_confidence_level()}")
        
        if self.assigned_team:
            parts.append(f"Team: {self.assigned_team}")
        
        return " | ".join(parts)
