"""
Defect Parser - Parses and validates defect descriptions
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging


class DefectParser:
    """Parse and structure defect information from various sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, defect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw defect data into structured format
        
        Args:
            defect_data: Raw defect information
            
        Returns:
            Structured defect object
        """
        self.logger.info(f"Parsing defect: {defect_data.get('id', 'unknown')}")
        
        structured_defect = {
            "id": defect_data.get("id"),
            "title": defect_data.get("title", defect_data.get("summary", "")),
            "description": self._clean_description(defect_data.get("description", "")),
            "severity": defect_data.get("severity", "medium"),
            "priority": defect_data.get("priority", "medium"),
            "status": defect_data.get("status", "open"),
            "reporter": defect_data.get("reporter"),
            "timestamp": self._parse_timestamp(defect_data.get("timestamp")),
            "environment": defect_data.get("environment", {}),
            "reproduction_steps": defect_data.get("reproduction_steps", []),
            "expected_behavior": defect_data.get("expected_behavior", ""),
            "actual_behavior": defect_data.get("actual_behavior", ""),
            "attachments": defect_data.get("attachments", []),
        }
        
        # Validate required fields
        self._validate(structured_defect)
        
        return structured_defect
    
    def _clean_description(self, description: str) -> str:
        """Clean and normalize defect description"""
        # Remove excessive whitespace
        cleaned = " ".join(description.split())
        return cleaned
    
    def _parse_timestamp(self, timestamp: Optional[str]) -> str:
        """Parse and normalize timestamp"""
        if not timestamp:
            return datetime.now().isoformat()
        
        # Add timestamp parsing logic here
        return timestamp
    
    def _validate(self, defect: Dict[str, Any]) -> None:
        """Validate defect data"""
        required_fields = ["id", "description"]
        
        for field in required_fields:
            if not defect.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        self.logger.debug(f"Defect validation successful: {defect['id']}")
