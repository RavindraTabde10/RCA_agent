"""
RCA Dashboard Plugin

Real-time monitoring dashboard for RCA analysis.
Tracks ticket progress, token consumption, and analysis metrics.

Usage:
    from rca_infotainment.dashboard import RCADashboard
    
    # Start dashboard
    dashboard = RCADashboard(port=5050)
    dashboard.start()
    
    # Track analysis
    dashboard.start_analysis("SAM1-2001", {"summary": "...", "component": "Media"})
    dashboard.update_stage("SAM1-2001", "dlt_analysis", "running")
    dashboard.add_tokens("SAM1-2001", "dlt_analysis", input_tokens=500, output_tokens=200)
    dashboard.update_stage("SAM1-2001", "dlt_analysis", "completed")
    dashboard.complete_analysis("SAM1-2001", success=True)
"""

from .dashboard_server import RCADashboard, DashboardState
from .tracker import AnalysisTracker, get_tracker

__all__ = [
    "RCADashboard",
    "DashboardState", 
    "AnalysisTracker",
    "get_tracker"
]
