"""
Time Analyzer - Analyzes temporal patterns and relationships
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging


class TimeAnalyzer:
    """Analyze time-based patterns in defect occurrence"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_temporal_patterns(
        self, 
        defect_timestamp: str,
        related_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze temporal patterns around defect occurrence
        
        Args:
            defect_timestamp: When the defect occurred
            related_events: List of related events with timestamps
            
        Returns:
            Temporal analysis results
        """
        self.logger.info(f"Analyzing temporal patterns for timestamp: {defect_timestamp}")
        
        analysis = {
            "defect_time": defect_timestamp,
            "time_of_day": self._get_time_of_day(defect_timestamp),
            "day_of_week": self._get_day_of_week(defect_timestamp),
            "frequency": "single",
            "pattern": "isolated",
            "correlated_events": [],
            "time_window": {
                "before": [],
                "during": [],
                "after": []
            }
        }
        
        # Analyze related events
        if related_events:
            analysis["correlated_events"] = self._find_correlated_events(
                defect_timestamp, related_events
            )
            analysis["frequency"] = self._determine_frequency(related_events)
            analysis["pattern"] = self._identify_pattern(related_events)
        
        return analysis
    
    def _get_time_of_day(self, timestamp: str) -> str:
        """Determine time of day category"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            
            if 0 <= hour < 6:
                return "night"
            elif 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 18:
                return "afternoon"
            else:
                return "evening"
        except Exception as e:
            self.logger.error(f"Error parsing timestamp: {e}")
            return "unknown"
    
    def _get_day_of_week(self, timestamp: str) -> str:
        """Get day of week from timestamp"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%A")
        except Exception as e:
            self.logger.error(f"Error parsing timestamp: {e}")
            return "unknown"
    
    def _find_correlated_events(
        self, 
        defect_timestamp: str,
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find events that occurred around the same time"""
        correlated = []
        
        try:
            defect_dt = datetime.fromisoformat(defect_timestamp.replace('Z', '+00:00'))
            time_window = timedelta(hours=1)  # 1 hour window
            
            for event in events:
                event_time = event.get("timestamp")
                if event_time:
                    event_dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                    time_diff = abs((event_dt - defect_dt).total_seconds())
                    
                    if time_diff <= time_window.total_seconds():
                        correlated.append({
                            "event": event,
                            "time_difference_seconds": time_diff
                        })
        except Exception as e:
            self.logger.error(f"Error finding correlated events: {e}")
        
        return sorted(correlated, key=lambda x: x["time_difference_seconds"])
    
    def _determine_frequency(self, events: List[Dict[str, Any]]) -> str:
        """Determine if defect is recurring"""
        if len(events) > 10:
            return "frequent"
        elif len(events) > 3:
            return "occasional"
        else:
            return "rare"
    
    def _identify_pattern(self, events: List[Dict[str, Any]]) -> str:
        """Identify temporal patterns"""
        if len(events) < 2:
            return "isolated"
        
        # Analyze event distribution
        # This is a simplified version
        timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
        
        if len(timestamps) < 2:
            return "isolated"
        
        # Check if events are clustered or distributed
        # Add more sophisticated pattern detection here
        
        return "clustered"
    
    def calculate_duration(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Calculate duration between two timestamps"""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end_dt - start_dt
            
            return {
                "seconds": duration.total_seconds(),
                "minutes": duration.total_seconds() / 60,
                "hours": duration.total_seconds() / 3600,
                "human_readable": str(duration)
            }
        except Exception as e:
            self.logger.error(f"Error calculating duration: {e}")
            return {"error": str(e)}
