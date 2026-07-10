"""
RCA Real-Time Dashboard - Analysis Monitor Plugin

This plugin provides a real-time monitoring dashboard that shows:
- Live ticket analysis progress
- Token consumption per ticket and total
- Confidence scores and stage progress
- Historical analysis metrics

Uses Server-Sent Events (SSE) for live updates without page refresh.
Designed as a standalone plugin - doesn't modify existing RCA framework.

Usage:
    from rca_dashboard import RCADashboard, AnalysisTracker
    
    # Start dashboard server
    dashboard = RCADashboard(port=5050)
    dashboard.start()
    
    # Track analysis
    tracker = AnalysisTracker()
    tracker.start_analysis("SAM1-2001", {"summary": "USB issue..."})
    tracker.update_stage("dlt_analysis", "running", tokens=1500)
    tracker.update_stage("dlt_analysis", "completed", tokens=2000)
    tracker.complete_analysis(confidence=0.87, root_cause="...")
"""

import os
import json
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Model Pricing Configuration (from copilot_consumption.py reference)
# ============================================================================

MODEL_MULTIPLIERS: Dict[str, float] = {
    # Free models
    'gpt-4.1': 0.0, 'gpt-4o': 0.0, 'gpt-5-mini': 0.0,
    # Lightweight premium
    'claude-haiku': 0.33, 'gemini-flash': 0.33,
    # Standard premium
    'claude-sonnet-4': 1.0, 'claude-sonnet': 1.0, 'gpt-5': 1.0, 'gemini-pro': 1.0,
    # Heavy premium
    'claude-opus-4': 3.0, 'claude-opus': 3.0,
}

DEFAULT_EURO_RATE = 37.0  # Per 1000 quota units


def get_model_multiplier(model: str) -> float:
    """Get quota multiplier for a model."""
    model_lower = model.lower()
    if model_lower in MODEL_MULTIPLIERS:
        return MODEL_MULTIPLIERS[model_lower]
    for key, mult in MODEL_MULTIPLIERS.items():
        if key in model_lower:
            return mult
    return 1.0  # Default to standard


# ============================================================================
# Data Classes for Tracking
# ============================================================================

@dataclass
class StageMetrics:
    """Metrics for a single analysis stage."""
    name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    quota_cost: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TicketAnalysis:
    """Complete analysis tracking for a single ticket."""
    ticket_id: str
    summary: str = ""
    component: str = ""
    priority: str = ""
    status: str = "queued"  # queued, running, completed, failed
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0
    
    # Stages
    stages: Dict[str, StageMetrics] = field(default_factory=dict)
    current_stage: str = ""
    
    # Token metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_quota_cost: float = 0
    estimated_cost_eur: float = 0
    
    # Results
    confidence: float = 0.0
    domain: str = ""
    root_cause: str = ""
    affected_files: List[str] = field(default_factory=list)
    historical_matches: int = 0
    
    # Model usage
    model: str = "unknown"
    model_breakdown: Dict[str, Dict] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stages"] = {k: v.to_dict() if isinstance(v, StageMetrics) else v 
                       for k, v in self.stages.items()}
        return d


@dataclass 
class DashboardState:
    """Global dashboard state."""
    active_analyses: Dict[str, TicketAnalysis] = field(default_factory=dict)
    completed_analyses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Global metrics
    total_tickets_analyzed: int = 0
    total_tokens_used: int = 0
    total_quota_cost: float = 0
    total_cost_eur: float = 0
    
    # Session info
    session_start: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_analyses": {k: v.to_dict() for k, v in self.active_analyses.items()},
            "completed_analyses": self.completed_analyses[-20:],  # Last 20
            "metrics": {
                "total_tickets": self.total_tickets_analyzed,
                "total_tokens": self.total_tokens_used,
                "total_quota_cost": self.total_quota_cost,
                "total_cost_eur": self.total_cost_eur,
                "session_duration_sec": time.time() - self.session_start,
                "active_count": len(self.active_analyses)
            }
        }


# ============================================================================
# Analysis Tracker - Core tracking logic
# ============================================================================

class AnalysisTracker:
    """
    Tracks RCA analysis progress and metrics in real-time.
    
    Usage:
        tracker = AnalysisTracker()
        
        # Start tracking a ticket
        tracker.start_analysis("SAM1-2001", {
            "summary": "USB issue...",
            "component": "Media",
            "priority": "High"
        })
        
        # Update stage progress
        tracker.update_stage("dlt_analysis", "running")
        tracker.add_tokens("dlt_analysis", input_tokens=500, output_tokens=200)
        tracker.update_stage("dlt_analysis", "completed")
        
        # Complete analysis
        tracker.complete_analysis("SAM1-2001", confidence=0.87, root_cause="...")
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global tracking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.state = DashboardState()
        self.event_queue: queue.Queue = queue.Queue()
        self.listeners: List[Callable] = []
        self._euro_rate = DEFAULT_EURO_RATE
        self._data_dir = Path("output/dashboard_data")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load persisted state
        self._load_state()
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all listeners and queue."""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Add to queue for SSE
        self.event_queue.put(event)
        
        # Notify listeners
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Listener error: {e}")
    
    def add_listener(self, callback: Callable):
        """Add event listener."""
        self.listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """Remove event listener."""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def start_analysis(
        self,
        ticket_id: str,
        defect_data: Dict[str, Any] = None,
        model: str = "claude-sonnet"
    ):
        """Start tracking a new ticket analysis."""
        defect_data = defect_data or {}
        
        analysis = TicketAnalysis(
            ticket_id=ticket_id,
            summary=defect_data.get("summary", "")[:100],
            component=defect_data.get("component", "Unknown"),
            priority=defect_data.get("priority", "Medium"),
            status="running",
            model=model,
            stages={
                "defect_loading": StageMetrics(name="Defect Loading"),
                "dlt_analysis": StageMetrics(name="DLT Analysis"),
                "source_mapping": StageMetrics(name="Source Mapping"),
                "historical_match": StageMetrics(name="Historical Match"),
                "llm_analysis": StageMetrics(name="LLM Analysis"),
                "report_generation": StageMetrics(name="Report Generation"),
            }
        )
        
        self.state.active_analyses[ticket_id] = analysis
        
        self._emit_event("analysis_started", {
            "ticket_id": ticket_id,
            "summary": analysis.summary,
            "component": analysis.component,
            "priority": analysis.priority
        })
        
        logger.info(f"Started tracking analysis for {ticket_id}")
    
    def update_stage(
        self,
        ticket_id: str,
        stage: str,
        status: str,
        error: str = None
    ):
        """Update stage status."""
        if ticket_id not in self.state.active_analyses:
            return
        
        analysis = self.state.active_analyses[ticket_id]
        
        if stage not in analysis.stages:
            analysis.stages[stage] = StageMetrics(name=stage)
        
        stage_metrics = analysis.stages[stage]
        stage_metrics.status = status
        
        if status == "running":
            stage_metrics.start_time = time.time()
            analysis.current_stage = stage
        elif status in ("completed", "failed"):
            if stage_metrics.start_time:
                stage_metrics.end_time = time.time()
                stage_metrics.duration_ms = (stage_metrics.end_time - stage_metrics.start_time) * 1000
            
            if status == "failed":
                stage_metrics.error = error
        
        self._emit_event("stage_updated", {
            "ticket_id": ticket_id,
            "stage": stage,
            "status": status,
            "duration_ms": stage_metrics.duration_ms,
            "error": error
        })
    
    def add_tokens(
        self,
        ticket_id: str,
        stage: str = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = None
    ):
        """Add token consumption to tracking."""
        if ticket_id not in self.state.active_analyses:
            return
        
        analysis = self.state.active_analyses[ticket_id]
        total = input_tokens + output_tokens
        
        # Update model if provided
        if model:
            analysis.model = model
        
        # Calculate quota cost
        multiplier = get_model_multiplier(analysis.model)
        quota_cost = total * multiplier / 1000  # Per 1000 tokens
        cost_eur = quota_cost * self._euro_rate / 1000
        
        # Update stage metrics
        if stage and stage in analysis.stages:
            s = analysis.stages[stage]
            s.input_tokens += input_tokens
            s.output_tokens += output_tokens
            s.total_tokens += total
            s.quota_cost += quota_cost
        
        # Update analysis totals
        analysis.total_input_tokens += input_tokens
        analysis.total_output_tokens += output_tokens
        analysis.total_tokens += total
        analysis.total_quota_cost += quota_cost
        analysis.estimated_cost_eur += cost_eur
        
        # Update model breakdown
        model_name = analysis.model
        if model_name not in analysis.model_breakdown:
            analysis.model_breakdown[model_name] = {
                "count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "quota_cost": 0,
                "multiplier": multiplier
            }
        mb = analysis.model_breakdown[model_name]
        mb["count"] += 1
        mb["input_tokens"] += input_tokens
        mb["output_tokens"] += output_tokens
        mb["total_tokens"] += total
        mb["quota_cost"] += quota_cost
        
        # Update global metrics
        self.state.total_tokens_used += total
        self.state.total_quota_cost += quota_cost
        self.state.total_cost_eur += cost_eur
        
        self._emit_event("tokens_added", {
            "ticket_id": ticket_id,
            "stage": stage,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total,
            "quota_cost": quota_cost,
            "cost_eur": cost_eur,
            "cumulative_tokens": analysis.total_tokens
        })
    
    def update_results(
        self,
        ticket_id: str,
        confidence: float = None,
        domain: str = None,
        root_cause: str = None,
        affected_files: List[str] = None,
        historical_matches: int = None
    ):
        """Update analysis results."""
        if ticket_id not in self.state.active_analyses:
            return
        
        analysis = self.state.active_analyses[ticket_id]
        
        if confidence is not None:
            analysis.confidence = confidence
        if domain:
            analysis.domain = domain
        if root_cause:
            analysis.root_cause = root_cause[:200]
        if affected_files:
            analysis.affected_files = affected_files[:10]
        if historical_matches is not None:
            analysis.historical_matches = historical_matches
        
        self._emit_event("results_updated", {
            "ticket_id": ticket_id,
            "confidence": analysis.confidence,
            "domain": analysis.domain,
            "historical_matches": analysis.historical_matches
        })
    
    def complete_analysis(
        self,
        ticket_id: str,
        success: bool = True,
        error: str = None
    ):
        """Complete analysis tracking."""
        if ticket_id not in self.state.active_analyses:
            return
        
        analysis = self.state.active_analyses[ticket_id]
        analysis.status = "completed" if success else "failed"
        analysis.end_time = time.time()
        analysis.duration_ms = (analysis.end_time - analysis.start_time) * 1000
        
        # Move to completed
        completed_data = analysis.to_dict()
        self.state.completed_analyses.append(completed_data)
        self.state.total_tickets_analyzed += 1
        
        # Remove from active
        del self.state.active_analyses[ticket_id]
        
        self._emit_event("analysis_completed", {
            "ticket_id": ticket_id,
            "success": success,
            "duration_ms": analysis.duration_ms,
            "total_tokens": analysis.total_tokens,
            "confidence": analysis.confidence,
            "error": error
        })
        
        # Persist state
        self._save_state()
        
        logger.info(f"Completed analysis for {ticket_id}: tokens={analysis.total_tokens}, confidence={analysis.confidence:.0%}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current dashboard state."""
        return self.state.to_dict()
    
    def get_analysis(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get specific analysis data."""
        if ticket_id in self.state.active_analyses:
            return self.state.active_analyses[ticket_id].to_dict()
        
        for completed in self.state.completed_analyses:
            if completed.get("ticket_id") == ticket_id:
                return completed
        
        return None
    
    def _save_state(self):
        """Persist state to disk."""
        try:
            state_file = self._data_dir / "dashboard_state.json"
            data = {
                "completed_analyses": self.state.completed_analyses[-100:],
                "metrics": {
                    "total_tickets": self.state.total_tickets_analyzed,
                    "total_tokens": self.state.total_tokens_used,
                    "total_quota_cost": self.state.total_quota_cost,
                    "total_cost_eur": self.state.total_cost_eur
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load persisted state."""
        try:
            state_file = self._data_dir / "dashboard_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    data = json.load(f)
                self.state.completed_analyses = data.get("completed_analyses", [])
                metrics = data.get("metrics", {})
                self.state.total_tickets_analyzed = metrics.get("total_tickets", 0)
                self.state.total_tokens_used = metrics.get("total_tokens", 0)
                self.state.total_quota_cost = metrics.get("total_quota_cost", 0)
                self.state.total_cost_eur = metrics.get("total_cost_eur", 0)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# ============================================================================
# Global tracker instance
# ============================================================================

_tracker: Optional[AnalysisTracker] = None

def get_tracker() -> AnalysisTracker:
    """Get global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = AnalysisTracker()
    return _tracker
