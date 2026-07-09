"""
Defect Model - Represents a defect/bug
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Defect:
    """Represents a software defect"""
    
    id: str
    title: str
    description: str
    severity: str = "medium"
    priority: str = "medium"
    status: str = "open"
    
    # Reporter and assignment
    reporter: Optional[str] = None
    assignee: Optional[str] = None
    assigned_team: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    resolved_at: Optional[str] = None
    
    # Environment and context
    environment: Dict[str, Any] = field(default_factory=dict)
    affected_versions: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    
    # Reproduction
    reproduction_steps: List[str] = field(default_factory=list)
    expected_behavior: str = ""
    actual_behavior: str = ""
    
    # Analysis
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    
    # Additional data
    logs: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    related_defects: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "priority": self.priority,
            "status": self.status,
            "reporter": self.reporter,
            "assignee": self.assignee,
            "assigned_team": self.assigned_team,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "environment": self.environment,
            "affected_versions": self.affected_versions,
            "affected_components": self.affected_components,
            "reproduction_steps": self.reproduction_steps,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "root_cause": self.root_cause,
            "resolution": self.resolution,
            "logs": self.logs,
            "comments": self.comments,
            "attachments": self.attachments,
            "related_defects": self.related_defects,
            "tags": self.tags,
            "custom_fields": self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Defect':
        """Create from dictionary"""
        return cls(**data)
    
    def add_comment(self, author: str, text: str):
        """Add a comment to the defect"""
        self.comments.append({
            "author": author,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_status(self, new_status: str):
        """Update defect status"""
        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        
        if new_status == "resolved":
            self.resolved_at = datetime.now().isoformat()
