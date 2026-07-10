"""
RCA Real-Time Dashboard Server

Simple HTTP server using Python's built-in http.server module.
No Flask or external frameworks required.

Features:
- Real-time updates via Server-Sent Events (SSE)
- Live token consumption tracking
- Ticket analysis progress monitoring
- Dark theme matching HTML report style

Usage:
    python dashboard_server.py
    # Opens http://localhost:5050 in browser
"""

import os
import sys
import json
import time
import threading
import queue
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import domain configuration
try:
    from rca_infotainment.domain_config import get_domain_config, get_domain_type
    _domain_config = get_domain_config()
    _domain_name = _domain_config.display_name
    _domain_type = _domain_config.domain.value
except ImportError:
    _domain_name = "Automotive"
    _domain_type = "automotive"

try:
    from dashboard.tracker import get_tracker, AnalysisTracker
except ImportError:
    # Standalone mode - define tracker inline
    pass


# ============================================================================
# Dashboard State (Standalone mode if tracker not available)
# ============================================================================

class DashboardState:
    """Global state for dashboard."""
    
    def __init__(self):
        self.active_analyses: Dict[str, Dict] = {}
        self.completed_analyses: List[Dict] = []
        self.events: queue.Queue = queue.Queue()
        self.token_timeline: List[Dict] = []  # Token events with timestamps
        self.metrics = {
            "total_tickets": 0,
            "total_tokens": 0,
            "total_cost_eur": 0.0,
            "session_start": time.time()
        }
        self._lock = threading.Lock()
    
    def add_token_event(self, ticket_id: str, stage: str, tokens: int, cost: float):
        """Record token consumption event with timestamp."""
        with self._lock:
            event = {
                "timestamp": datetime.now().isoformat(),
                "ts_unix": time.time(),
                "ticket_id": ticket_id,
                "stage": stage,
                "tokens": tokens,
                "cost_eur": cost,
                "cumulative_tokens": self.metrics.get('total_tokens', 0),
                "cumulative_cost": self.metrics.get('total_cost_eur', 0)
            }
            self.token_timeline.append(event)
            # Keep last 500 events
            if len(self.token_timeline) > 500:
                self.token_timeline = self.token_timeline[-500:]
    
    def add_event(self, event_type: str, data: Dict):
        """Add event for SSE broadcast."""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.events.put(event)
    
    def get_state(self) -> Dict:
        """Get current state."""
        with self._lock:
            return {
                "active_analyses": self.active_analyses.copy(),
                "completed_analyses": self.completed_analyses[-20:],
                "token_timeline": self.token_timeline[-100:],  # Last 100 events for chart
                "metrics": {
                    **self.metrics,
                    "session_duration": time.time() - self.metrics["session_start"],
                    "active_count": len(self.active_analyses)
                },
                "timestamp": datetime.now().isoformat()
            }


# Global state
_state = DashboardState()


# ============================================================================
# HTML Dashboard Template
# ============================================================================

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RCA Monitoring Dashboard</title>
  <style>
    :root {
      --bg-primary: #0f1117;
      --bg-secondary: #161822;
      --bg-card: #1c1f2e;
      --bg-hover: #252940;
      --border: #2a2e42;
      --text-primary: #e4e6f0;
      --text-secondary: #9498b0;
      --text-muted: #6b6f88;
      --accent: #6c8cff;
      --accent-light: #8ba3ff;
      --success: #4ade80;
      --warning: #fbbf24;
      --error: #f87171;
      --info: #60a5fa;
    }
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.6;
      min-height: 100vh;
    }
    
    .header {
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      padding: 16px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    .logo {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--accent), var(--success));
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 12px;
      color: #fff;
    }
    
    .header h1 {
      font-size: 24px;
      font-weight: 600;
    }
    
    .header h1 span {
      color: var(--text-muted);
      font-weight: 400;
      font-size: 16px;
      margin-left: 8px;
    }
    
    .connection-status {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: var(--bg-card);
      border-radius: 20px;
      font-size: 13px;
    }
    
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--error);
      animation: pulse 2s infinite;
    }
    
    .status-dot.connected {
      background: var(--success);
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    .main-content {
      padding: 16px 24px;
      max-width: 1800px;
      margin: 0 auto;
      min-height: calc(100vh - 80px);
      overflow-y: auto;
    }
    
    /* Two Column Layout */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: auto minmax(300px, 400px);
      gap: 16px;
    }
    
    .metrics-row {
      grid-column: 1 / -1;
    }
    
    .left-panel {
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-height: 0;
      overflow: hidden;
    }
    
    .right-panel {
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-height: 0;
      overflow: hidden;
    }
    
    /* Metrics Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 12px;
    }
    
    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      transition: transform 0.2s, border-color 0.2s;
    }
    
    .metric-card:hover {
      border-color: var(--accent);
    }
    
    .metric-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-bottom: 4px;
    }
    
    .metric-value {
      font-size: 22px;
      font-weight: 700;
      color: var(--text-primary);
    }
    
    .metric-value.accent { color: var(--accent-light); }
    .metric-value.success { color: var(--success); }
    .metric-value.warning { color: var(--warning); }
    .metric-value.info { color: var(--info); }
    
    .metric-change {
      font-size: 10px;
      color: var(--text-muted);
      margin-top: 2px;
    }
    
    /* Section */
    .section {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      min-height: 0;
      overflow: hidden;
    }
    
    .section.flex-1 {
      flex: 1;
    }
    
    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
    }
    
    .section-title {
      font-size: 14px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .section-title .icon {
      font-size: 16px;
    }
    
    .section-content {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }
    
    #tokenEventsContainer {
      max-height: 150px;
      overflow-y: scroll !important;
    }
    
    .badge {
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .badge-accent { background: rgba(108, 140, 255, 0.15); color: var(--accent-light); }
    .badge-success { background: rgba(74, 222, 128, 0.12); color: var(--success); }
    .badge-warning { background: rgba(251, 191, 36, 0.12); color: var(--warning); }
    
    /* Active Analysis Cards */
    .analysis-grid {
      padding: 12px;
    }
    
    .analysis-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 12px;
    }
    
    .analysis-card:last-child {
      margin-bottom: 0;
    }
    
    .analysis-card.running {
      border-left: 3px solid var(--accent);
      animation: borderPulse 2s infinite;
    }
    
    @keyframes borderPulse {
      0%, 100% { border-left-color: var(--accent); }
      50% { border-left-color: var(--success); }
    }
    
    .analysis-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    
    .ticket-id {
      font-size: 14px;
      font-weight: 600;
      color: var(--accent-light);
    }
    
    .ticket-summary {
      font-size: 11px;
      color: var(--text-secondary);
      margin-top: 2px;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .analysis-status {
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .status-running {
      background: rgba(108, 140, 255, 0.15);
      color: var(--accent-light);
    }
    
    .status-completed {
      background: rgba(74, 222, 128, 0.12);
      color: var(--success);
    }
    
    /* Progress Stages */
    .stages-progress {
      margin: 8px 0;
    }
    
    .stage-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      font-size: 12px;
    }
    
    .stage-indicator {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      flex-shrink: 0;
    }
    
    .stage-pending {
      background: var(--bg-hover);
      color: var(--text-muted);
    }
    
    .stage-running {
      background: var(--accent);
      color: #fff;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    .stage-completed {
      background: var(--success);
      color: #fff;
    }
    
    .stage-failed {
      background: var(--error);
      color: #fff;
    }
    
    .stage-name {
      flex: 1;
      font-size: 11px;
      color: var(--text-secondary);
    }
    
    .stage-tokens {
      font-size: 10px;
      color: var(--text-muted);
      font-family: monospace;
    }
    
    .stage-duration {
      font-size: 10px;
      color: var(--text-muted);
      min-width: 40px;
      text-align: right;
    }
    
    /* Token Metrics */
    .token-metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--border);
    }
    
    .token-metric {
      text-align: center;
    }
    
    .token-metric-value {
      font-size: 14px;
      font-weight: 600;
      font-family: monospace;
    }
    
    .token-metric-label {
      font-size: 9px;
      color: var(--text-muted);
      text-transform: uppercase;
    }
    
    /* Confidence Meter */
    .confidence-meter {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }
    
    .confidence-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    
    .confidence-label {
      font-size: 13px;
      color: var(--text-secondary);
    }
    
    .confidence-value {
      font-size: 18px;
      font-weight: 600;
      color: var(--success);
    }
    
    .confidence-bar {
      height: 8px;
      background: var(--bg-hover);
      border-radius: 4px;
      overflow: hidden;
    }
    
    .confidence-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--warning), var(--success));
      border-radius: 4px;
      transition: width 0.5s ease;
    }
    
    /* History Table */
    .history-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    
    .history-table th {
      text-align: left;
      padding: 12px 16px;
      background: var(--bg-card);
      color: var(--text-muted);
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      border-bottom: 2px solid var(--border);
    }
    
    .history-table td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      color: var(--text-secondary);
    }
    
    .history-table tbody tr:hover {
      background: var(--bg-hover);
    }
    
    .history-table .ticket-link {
      color: var(--accent-light);
      text-decoration: none;
      font-weight: 500;
    }
    
    /* Event Log */
    .event-log {
      flex: 1;
      overflow-y: scroll !important;
      scroll-behavior: auto;
      min-height: 0;
    }

    .event-item {
      padding: 8px 12px;
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      display: flex;
      gap: 10px;
      animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; background: rgba(108, 140, 255, 0.1); }
      to { opacity: 1; background: transparent; }
    }
    
    .event-item:last-child {
      border-bottom: none;
    }
    
    .event-time {
      color: var(--text-muted);
      font-family: monospace;
      font-size: 10px;
      min-width: 60px;
    }
    
    .event-type {
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 500;
      min-width: 70px;
      text-align: center;
    }
    
    .event-type.start { background: rgba(108, 140, 255, 0.15); color: var(--accent-light); }
    .event-type.stage { background: rgba(251, 191, 36, 0.12); color: var(--warning); }
    .event-type.tokens { background: rgba(96, 165, 250, 0.12); color: var(--info); }
    .event-type.complete { background: rgba(74, 222, 128, 0.12); color: var(--success); }
    
    .event-message {
      flex: 1;
      color: var(--text-secondary);
    }
    
    /* Empty State */
    .empty-state {
      text-align: center;
      padding: 48px;
      color: var(--text-muted);
    }
    
    .empty-state .icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
    
    /* Token Timeline Chart */
    .timeline-chart {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 32px;
    }
    
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    
    .chart-title {
      font-size: 16px;
      font-weight: 600;
    }
    
    .chart-stats {
      display: flex;
      gap: 20px;
      font-size: 12px;
      color: var(--text-secondary);
    }
    
    .chart-stat-value {
      font-weight: 600;
      color: var(--text-primary);
      margin-left: 4px;
    }
    
    .chart-container {
      position: relative;
      height: 200px;
      margin-bottom: 16px;
    }
    
    #tokenChart {
      width: 100%;
      height: 100%;
    }
    
    .chart-legend {
      display: flex;
      justify-content: center;
      gap: 24px;
      font-size: 12px;
      color: var(--text-secondary);
    }
    
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    
    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    
    .legend-tokens { background: var(--accent); }
    .legend-cost { background: var(--success); }
    
    /* Token Timeline Table */
    .timeline-table-container {
      max-height: 250px;
      overflow-y: auto;
      scroll-behavior: smooth;
    }
    
    .timeline-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    
    .timeline-table th {
      text-align: left;
      padding: 10px 12px;
      background: var(--bg-hover);
      color: var(--text-muted);
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      position: sticky;
      top: 0;
      z-index: 1;
    }
    
    .timeline-table td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      color: var(--text-secondary);
    }
    
    .timeline-table tbody tr {
      animation: fadeIn 0.3s ease;
    }
    
    .timeline-table tbody tr:hover {
      background: var(--bg-hover);
    }
    
    .timeline-table .ts { color: var(--text-muted); font-family: monospace; font-size: 11px; }
    .timeline-table .ticket { color: var(--accent-light); font-weight: 500; }
    .timeline-table .stage { color: var(--warning); }
    .timeline-table .tokens { color: var(--info); font-family: monospace; }
    .timeline-table .cost { color: var(--success); font-family: monospace; }
    .timeline-table .cumulative { color: var(--text-muted); font-family: monospace; }

    /* Footer */
    .footer {
      text-align: center;
      padding: 24px;
      color: var(--text-muted);
      font-size: 12px;
      border-top: 1px solid var(--border);
      margin-top: 48px;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
      .main-content { padding: 16px; }
      .metrics-grid { grid-template-columns: repeat(2, 1fr); }
      .analysis-grid { grid-template-columns: 1fr; }
      .header { padding: 12px 16px; }
    }
  </style>
</head>
<body>
  <header class="header">
    <div class="header-left">
      <div class="logo">RCA</div>
      <h1>RCA MONITORING DASHBOARD</h1>
      <div style="margin-left: 16px; padding: 4px 10px; background: rgba(108, 140, 255, 0.15); border-radius: 12px; font-size: 11px; color: #6c8cff; font-weight: 500;">
        {domain_display_name}
      </div>
    </div>
    <div class="connection-status">
      <div class="status-dot" id="connectionDot"></div>
      <span id="connectionText">Connecting...</span>
    </div>
  </header>
  
  <main class="main-content">
    <div class="dashboard-grid">
      <!-- Metrics Row -->
      <div class="metrics-row">
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-label">Tickets</div>
            <div class="metric-value accent" id="metricTickets">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Tokens</div>
            <div class="metric-value info" id="metricTokens">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Quota</div>
            <div class="metric-value warning" id="metricQuota">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Cost</div>
            <div class="metric-value success" id="metricCost">€0.00</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Active</div>
            <div class="metric-value" id="metricActive">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Session</div>
            <div class="metric-value" id="metricSession">00:00</div>
          </div>
        </div>
      </div>
      
      <!-- Left Panel: Active Analyses + Token Events -->
      <div class="left-panel">
        <!-- Active Analyses -->
        <div class="section flex-1">
          <div class="section-header">
            <div class="section-title">
              <span class="icon">⚡</span>
              Active Analyses
            </div>
            <span class="badge badge-accent" id="activeCount">0 running</span>
          </div>
          <div class="section-content">
            <div class="analysis-grid" id="activeAnalyses">
              <div style="padding: 20px; text-align: center; color: var(--text-muted);">
                <div style="font-size: 24px; margin-bottom: 8px;">📊</div>
                <p style="font-size: 12px;">No active analyses</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Token Events Table -->
        <div class="section" style="max-height: 200px;">
          <div class="section-header">
            <div class="section-title">
              <span class="icon">💰</span>
              Token Events
            </div>
            <span style="font-size: 11px; color: var(--text-muted);" id="tokenEventCount">0 events</span>
          </div>
          <div class="section-content" id="tokenEventsContainer">
            <table class="timeline-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Ticket</th>
                  <th>Stage</th>
                  <th>+Tokens</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody id="tokenTimelineBody">
                <tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px; font-size: 11px;">No token events</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- Right Panel: Live Event Log + Recent History -->
      <div class="right-panel">
        <!-- Live Event Log -->
        <div class="section flex-1">
          <div class="section-header">
            <div class="section-title">
              <span class="icon">📜</span>
              Live Event Log
            </div>
            <div style="display: flex; gap: 6px; align-items: center;">
              <label style="display: flex; align-items: center; gap: 4px; font-size: 10px; color: var(--text-secondary); cursor: pointer;">
                <input type="checkbox" id="autoScrollToggle" checked style="cursor: pointer; width: 12px; height: 12px;"> Auto
              </label>
              <button onclick="clearEvents()" style="background: var(--bg-hover); border: 1px solid var(--border); color: var(--text-secondary); padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 10px;">Clear</button>
            </div>
          </div>
          <div class="event-log" id="eventLog">
            <div class="event-item">
              <span class="event-time">--:--:--</span>
              <span class="event-type">info</span>
              <span class="event-message">Waiting for events...</span>
            </div>
          </div>
        </div>
        
        <!-- Recent History -->
        <div class="section" style="max-height: 180px;">
          <div class="section-header">
            <div class="section-title">
              <span class="icon">📋</span>
              Recent Analyses
            </div>
          </div>
          <div class="section-content">
            <table class="history-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Status</th>
                  <th>Conf.</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody id="historyBody">
                <tr>
                  <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px; font-size: 11px;">No completed analyses</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Token Timeline Chart (Bottom) -->
    <div class="section" style="margin-top: 16px; min-height: 220px;">
      <div class="section-header">
        <div class="section-title">
          <span class="icon">📈</span>
          Token Consumption Over Time
        </div>
        <div style="display: flex; gap: 16px; font-size: 11px; color: var(--text-secondary);">
          <span>Peak: <span style="color: var(--info); font-weight: 600;" id="chartPeak">0</span></span>
          <span>Avg: <span style="color: var(--warning); font-weight: 600;" id="chartAvg">0</span>/event</span>
          <span>Rate: <span style="color: var(--success); font-weight: 600;" id="chartRate">0</span>/min</span>
        </div>
      </div>
      <div id="chartContainer" style="padding: 12px; height: 160px; position: relative;">
        <canvas id="tokenChart" style="width: 100%; height: 100%;"></canvas>
      </div>
    </div>
  </main>
  
  <script>
    // State
    let state = {
      connected: false,
      metrics: { total_tickets: 0, total_tokens: 0, total_cost_eur: 0, session_start: Date.now() / 1000 },
      activeAnalyses: {},
      completedAnalyses: [],
      tokenTimeline: [],
      events: [],
      autoScroll: true
    };
    
    // SSE Connection
    let eventSource = null;
    
    // Chart context
    let chartCtx = null;
    let chartInitialized = false;
    
    function connect() {
      eventSource = new EventSource('/events');
      
      eventSource.onopen = () => {
        state.connected = true;
        updateConnectionStatus();
        addEvent('info', 'Connected to dashboard server');
      };
      
      eventSource.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data);
          handleEvent(event);
        } catch (err) {
          console.error('Parse error:', err);
        }
      };
      
      eventSource.onerror = () => {
        state.connected = false;
        updateConnectionStatus();
        addEvent('error', 'Connection lost, reconnecting...');
        
        eventSource.close();
        setTimeout(connect, 3000);
      };
    }
    
    function handleEvent(event) {
      const { type, data, timestamp } = event;
      
      switch (type) {
        case 'state':
          // Full state update
          state.metrics = data.metrics || state.metrics;
          state.activeAnalyses = data.active_analyses || {};
          state.completedAnalyses = data.completed_analyses || [];
          state.tokenTimeline = data.token_timeline || [];
          updateUI();
          updateTokenTimeline();
          break;
          
        case 'analysis_started':
          state.activeAnalyses[data.ticket_id] = {
            ticket_id: data.ticket_id,
            summary: data.summary,
            component: data.component,
            priority: data.priority,
            status: 'running',
            stages: {},
            total_tokens: 0,
            confidence: 0
          };
          addEvent('start', `Started analysis: ${data.ticket_id}`);
          updateUI();
          break;
          
        case 'stage_updated':
          if (state.activeAnalyses[data.ticket_id]) {
            const analysis = state.activeAnalyses[data.ticket_id];
            analysis.stages[data.stage] = {
              status: data.status,
              duration_ms: data.duration_ms || 0
            };
            analysis.current_stage = data.stage;
          }
          addEvent('stage', `${data.ticket_id}: ${data.stage} → ${data.status}`);
          updateUI();
          scrollToLatest();
          break;
          
        case 'tokens_added':
          if (state.activeAnalyses[data.ticket_id]) {
            const analysis = state.activeAnalyses[data.ticket_id];
            analysis.total_tokens = data.cumulative_tokens || 0;
            if (analysis.stages[data.stage]) {
              analysis.stages[data.stage].tokens = (analysis.stages[data.stage].tokens || 0) + data.total_tokens;
            }
          }
          state.metrics.total_tokens = (state.metrics.total_tokens || 0) + data.total_tokens;
          state.metrics.total_cost_eur = (state.metrics.total_cost_eur || 0) + data.cost_eur;
          // Add to timeline
          state.tokenTimeline.push({
            timestamp: timestamp,
            ts_unix: Date.now() / 1000,
            ticket_id: data.ticket_id,
            stage: data.stage,
            tokens: data.total_tokens,
            cost_eur: data.cost_eur,
            cumulative_tokens: state.metrics.total_tokens,
            cumulative_cost: state.metrics.total_cost_eur
          });
          if (state.tokenTimeline.length > 100) state.tokenTimeline = state.tokenTimeline.slice(-100);
          addEvent('tokens', `${data.ticket_id}: +${data.total_tokens} tokens (${data.stage})`);
          updateUI();
          updateTokenTimeline();
          scrollToLatest();
          break;
          
        case 'results_updated':
          if (state.activeAnalyses[data.ticket_id]) {
            state.activeAnalyses[data.ticket_id].confidence = data.confidence;
            state.activeAnalyses[data.ticket_id].domain = data.domain;
          }
          updateUI();
          break;
          
        case 'analysis_completed':
          const completed = state.activeAnalyses[data.ticket_id];
          if (completed) {
            completed.status = data.success ? 'completed' : 'failed';
            completed.duration_ms = data.duration_ms;
            completed.confidence = data.confidence;
            state.completedAnalyses.unshift(completed);
            delete state.activeAnalyses[data.ticket_id];
          }
          state.metrics.total_tickets = (state.metrics.total_tickets || 0) + 1;
          addEvent('complete', `Completed: ${data.ticket_id} (${data.success ? 'success' : 'failed'})`);
          updateUI();
          scrollToLatest();
          break;
          
        case 'heartbeat':
          // Keep-alive
          break;
      }
    }
    
    function addEvent(type, message) {
      const now = new Date();
      const time = now.toTimeString().split(' ')[0];
      state.events.unshift({ type, message, time });
      state.events = state.events.slice(0, 50); // Keep last 50
      updateEventLog();
      debouncedScroll();
    }
    
    function clearEvents() {
      state.events = [];
      updateEventLog();
    }
    
    // Debounced scroll to prevent conflicts
    let scrollTimeout = null;
    function debouncedScroll() {
      if (scrollTimeout) clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(doScroll, 20);
    }
    
    function doScroll() {
      if (!state.autoScroll) return;
      
      // Use double RAF to ensure DOM is fully rendered
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          // Force scroll event log to top
          const eventLog = document.getElementById('eventLog');
          if (eventLog && eventLog.scrollHeight > eventLog.clientHeight) {
            eventLog.scrollTop = 0;
          }
          
          // Force scroll token events container to top
          const tokenContainer = document.getElementById('tokenEventsContainer');
          if (tokenContainer && tokenContainer.scrollHeight > tokenContainer.clientHeight) {
            tokenContainer.scrollTop = 0;
          }
          
          // Scroll active analyses to show current running stage
          const analysisGrid = document.getElementById('activeAnalyses');
          if (analysisGrid) {
            const container = analysisGrid.closest('.section-content');
            if (container) {
              const runningStage = container.querySelector('.stage-running');
              if (runningStage) {
                runningStage.closest('.stage-row')?.scrollIntoView({ behavior: 'auto', block: 'nearest' });
              }
            }
          }
        });
      });
    }
    
    function scrollToLatest() {
      debouncedScroll();
    }
    
    function updateConnectionStatus() {
      const dot = document.getElementById('connectionDot');
      const text = document.getElementById('connectionText');
      
      if (state.connected) {
        dot.classList.add('connected');
        text.textContent = 'Connected';
      } else {
        dot.classList.remove('connected');
        text.textContent = 'Disconnected';
      }
    }
    
    function updateUI() {
      updateMetrics();
      updateActiveAnalyses();
      updateHistory();
    }
    
    function updateMetrics() {
      const m = state.metrics;
      
      document.getElementById('metricTickets').textContent = m.total_tickets || 0;
      document.getElementById('metricTokens').textContent = formatNumber(m.total_tokens || 0);
      document.getElementById('metricQuota').textContent = formatNumber(Math.round(m.total_quota_cost || 0));
      document.getElementById('metricCost').textContent = '€' + (m.total_cost_eur || 0).toFixed(2);
      document.getElementById('metricActive').textContent = Object.keys(state.activeAnalyses).length;
      
      // Session time
      const sessionSec = m.session_duration || (Date.now() / 1000 - m.session_start);
      document.getElementById('metricSession').textContent = formatDuration(sessionSec * 1000);
      
      document.getElementById('activeCount').textContent = `${Object.keys(state.activeAnalyses).length} running`;
    }
    
    function updateActiveAnalyses() {
      const container = document.getElementById('activeAnalyses');
      const analyses = Object.values(state.activeAnalyses);
      
      if (analyses.length === 0) {
        container.innerHTML = `
          <div style="padding: 20px; text-align: center; color: var(--text-muted);">
            <div style="font-size: 24px; margin-bottom: 8px;">📊</div>
            <p style="font-size: 12px;">No active analyses</p>
          </div>
        `;
        return;
      }
      
      container.innerHTML = analyses.map(a => renderAnalysisCard(a)).join('');
    }
    
    function renderAnalysisCard(analysis) {
      const stages = [
        { key: 'defect_loading', name: 'Defect Loading' },
        { key: 'dlt_analysis', name: 'DLT Analysis' },
        { key: 'source_mapping', name: 'Source Mapping' },
        { key: 'historical_match', name: 'Historical Match' },
        { key: 'llm_analysis', name: 'LLM Analysis' },
        { key: 'report_generation', name: 'Report Generation' }
      ];
      
      const stagesHtml = stages.map(s => {
        const stage = analysis.stages[s.key] || {};
        const status = stage.status || 'pending';
        const tokens = stage.tokens || 0;
        const duration = stage.duration_ms || 0;
        
        let indicator = '○';
        let indicatorClass = 'stage-pending';
        if (status === 'running') {
          indicator = '◌';
          indicatorClass = 'stage-running';
        } else if (status === 'completed') {
          indicator = '✓';
          indicatorClass = 'stage-completed';
        } else if (status === 'failed') {
          indicator = '✗';
          indicatorClass = 'stage-failed';
        }
        
        return `
          <div class="stage-row">
            <div class="stage-indicator ${indicatorClass}">${indicator}</div>
            <div class="stage-name">${s.name}</div>
            <div class="stage-tokens">${tokens > 0 ? tokens + ' tok' : ''}</div>
            <div class="stage-duration">${duration > 0 ? formatDuration(duration) : ''}</div>
          </div>
        `;
      }).join('');
      
      const confidence = analysis.confidence || 0;
      
      return `
        <div class="analysis-card running">
          <div class="analysis-header">
            <div>
              <div class="ticket-id">${analysis.ticket_id}</div>
              <div class="ticket-summary">${analysis.summary || 'No summary'}</div>
            </div>
            <div class="analysis-status status-running">
              ${analysis.current_stage || 'Starting...'}
            </div>
          </div>
          
          <div class="stages-progress">
            ${stagesHtml}
          </div>
          
          <div class="token-metrics">
            <div class="token-metric">
              <div class="token-metric-value" style="color: var(--info);">${formatNumber(analysis.total_tokens || 0)}</div>
              <div class="token-metric-label">Total Tokens</div>
            </div>
            <div class="token-metric">
              <div class="token-metric-value" style="color: var(--warning);">${analysis.component || '-'}</div>
              <div class="token-metric-label">Component</div>
            </div>
            <div class="token-metric">
              <div class="token-metric-value" style="color: var(--accent-light);">${analysis.priority || '-'}</div>
              <div class="token-metric-label">Priority</div>
            </div>
          </div>
          
          ${confidence > 0 ? `
          <div class="confidence-meter">
            <div class="confidence-header">
              <span class="confidence-label">Confidence</span>
              <span class="confidence-value">${Math.round(confidence * 100)}%</span>
            </div>
            <div class="confidence-bar">
              <div class="confidence-fill" style="width: ${confidence * 100}%"></div>
            </div>
          </div>
          ` : ''}
        </div>
      `;
    }
    
    function updateHistory() {
      const tbody = document.getElementById('historyBody');
      const analyses = state.completedAnalyses.slice(0, 10);
      
      if (analyses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px; font-size: 11px;">No completed analyses</td></tr>';
        return;
      }
      
      tbody.innerHTML = analyses.map(a => `
        <tr>
          <td><span class="ticket-link">${a.ticket_id}</span></td>
          <td><span class="badge ${a.status === 'completed' ? 'badge-success' : 'badge-warning'}">${a.status === 'completed' ? '✓' : '✗'}</span></td>
          <td>${a.confidence ? Math.round(a.confidence * 100) + '%' : '-'}</td>
          <td>${formatNumber(a.total_tokens || 0)}</td>
          <td>€${((a.total_tokens || 0) * 0.000037).toFixed(2)}</td>
        </tr>
      `).join('');
    }
    
    function updateEventLog() {
      const log = document.getElementById('eventLog');
      
      if (state.events.length === 0) {
        log.innerHTML = `
          <div class="event-item">
            <span class="event-time">--:--:--</span>
            <span class="event-type">info</span>
            <span class="event-message">Waiting for events...</span>
          </div>
        `;
        return;
      }
      
      log.innerHTML = state.events.map(e => `
        <div class="event-item">
          <span class="event-time">${e.time}</span>
          <span class="event-type ${e.type}">${e.type}</span>
          <span class="event-message">${e.message}</span>
        </div>
      `).join('');
    }
    
    // Token Timeline Chart
    function initChart() {
      const canvas = document.getElementById('tokenChart');
      const container = document.getElementById('chartContainer');
      if (!canvas || !container) return;
      
      // Set canvas size based on container
      const rect = container.getBoundingClientRect();
      const width = rect.width - 24; // Account for padding
      const height = rect.height - 24;
      
      canvas.width = width * 2;
      canvas.height = height * 2;
      canvas.style.width = width + 'px';
      canvas.style.height = height + 'px';
      
      chartCtx = canvas.getContext('2d');
      chartCtx.scale(2, 2);
      chartInitialized = true;
    }
    
    function updateTokenTimeline() {
      const timeline = state.tokenTimeline;
      
      // Update event count
      document.getElementById('tokenEventCount').textContent = `${timeline.length} events`;
      
      // Update table
      updateTokenTimelineTable();
      
      // Update chart
      if (!chartInitialized) initChart();
      if (chartCtx) drawChart();
      
      // Update stats
      if (timeline.length > 0) {
        const tokens = timeline.map(e => e.tokens);
        const maxTokens = Math.max(...tokens);
        const avgTokens = Math.round(tokens.reduce((a, b) => a + b, 0) / tokens.length);
        
        const firstTs = timeline[0].ts_unix || (Date.parse(timeline[0].timestamp) / 1000);
        const lastTs = timeline[timeline.length - 1].ts_unix || (Date.parse(timeline[timeline.length - 1].timestamp) / 1000);
        const durationMin = (lastTs - firstTs) / 60 || 1;
        const totalTok = timeline.reduce((a, e) => a + e.tokens, 0);
        const rate = Math.round(totalTok / durationMin);
        
        document.getElementById('chartPeak').textContent = formatNumber(maxTokens);
        document.getElementById('chartAvg').textContent = formatNumber(avgTokens);
        document.getElementById('chartRate').textContent = formatNumber(rate);
      }
    }
    
    function drawChart() {
      const canvas = document.getElementById('tokenChart');
      const container = document.getElementById('chartContainer');
      if (!canvas || !chartCtx || !container) return;
      
      const rect = container.getBoundingClientRect();
      const width = rect.width - 24;
      const height = rect.height - 24;
      const timeline = state.tokenTimeline;
      
      chartCtx.clearRect(0, 0, width, height);
      
      if (timeline.length < 2) {
        chartCtx.fillStyle = '#6b6f88';
        chartCtx.font = '12px sans-serif';
        chartCtx.textAlign = 'center';
        chartCtx.fillText('Waiting for token data...', width / 2, height / 2);
        return;
      }
      
      const padding = { top: 10, right: 50, bottom: 20, left: 50 };
      const chartWidth = width - padding.left - padding.right;
      const chartHeight = height - padding.top - padding.bottom;
      
      const maxTokens = Math.max(...timeline.map(e => e.cumulative_tokens)) || 1;
      const maxCost = Math.max(...timeline.map(e => e.cumulative_cost)) || 0.01;
      
      // Draw grid
      chartCtx.strokeStyle = '#2a2e42';
      chartCtx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight * i / 4);
        chartCtx.beginPath();
        chartCtx.moveTo(padding.left, y);
        chartCtx.lineTo(width - padding.right, y);
        chartCtx.stroke();
        
        chartCtx.fillStyle = '#6b6f88';
        chartCtx.font = '9px monospace';
        chartCtx.textAlign = 'right';
        chartCtx.fillText(formatNumber(Math.round(maxTokens * (1 - i / 4))), padding.left - 5, y + 3);
        
        chartCtx.textAlign = 'left';
        chartCtx.fillText('€' + (maxCost * (1 - i / 4)).toFixed(2), width - padding.right + 5, y + 3);
      }
      
      // Draw token area fill
      chartCtx.beginPath();
      chartCtx.moveTo(padding.left, padding.top + chartHeight);
      timeline.forEach((e, i) => {
        const x = padding.left + (i / (timeline.length - 1)) * chartWidth;
        const y = padding.top + chartHeight - (e.cumulative_tokens / maxTokens * chartHeight);
        chartCtx.lineTo(x, y);
      });
      chartCtx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
      chartCtx.closePath();
      chartCtx.fillStyle = 'rgba(108, 140, 255, 0.15)';
      chartCtx.fill();
      
      // Draw token line
      chartCtx.strokeStyle = '#6c8cff';
      chartCtx.lineWidth = 2;
      chartCtx.beginPath();
      timeline.forEach((e, i) => {
        const x = padding.left + (i / (timeline.length - 1)) * chartWidth;
        const y = padding.top + chartHeight - (e.cumulative_tokens / maxTokens * chartHeight);
        if (i === 0) chartCtx.moveTo(x, y);
        else chartCtx.lineTo(x, y);
      });
      chartCtx.stroke();
      
      // Draw cost line
      chartCtx.strokeStyle = '#4ade80';
      chartCtx.lineWidth = 2;
      chartCtx.beginPath();
      timeline.forEach((e, i) => {
        const x = padding.left + (i / (timeline.length - 1)) * chartWidth;
        const y = padding.top + chartHeight - (e.cumulative_cost / maxCost * chartHeight);
        if (i === 0) chartCtx.moveTo(x, y);
        else chartCtx.lineTo(x, y);
      });
      chartCtx.stroke();
      
      // Draw points
      timeline.forEach((e, i) => {
        const x = padding.left + (i / (timeline.length - 1)) * chartWidth;
        const y = padding.top + chartHeight - (e.cumulative_tokens / maxTokens * chartHeight);
        chartCtx.beginPath();
        chartCtx.arc(x, y, 3, 0, Math.PI * 2);
        chartCtx.fillStyle = '#6c8cff';
        chartCtx.fill();
      });
      
      // Time labels
      chartCtx.fillStyle = '#6b6f88';
      chartCtx.font = '9px sans-serif';
      chartCtx.textAlign = 'center';
      const firstTs = new Date(timeline[0].timestamp).toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
      const lastTs = new Date(timeline[timeline.length - 1].timestamp).toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
      chartCtx.fillText(firstTs, padding.left, height - 5);
      chartCtx.fillText(lastTs, width - padding.right, height - 5);
      
      // Legend
      chartCtx.font = '10px sans-serif';
      chartCtx.fillStyle = '#6c8cff';
      chartCtx.fillText('● Tokens', width / 2 - 40, height - 5);
      chartCtx.fillStyle = '#4ade80';
      chartCtx.fillText('● Cost', width / 2 + 20, height - 5);
    }
    
    function updateTokenTimelineTable() {
      const tbody = document.getElementById('tokenTimelineBody');
      const container = tbody.closest('.section-content');
      const timeline = [...state.tokenTimeline].reverse().slice(0, 30); // Show last 30
      
      if (timeline.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px; font-size: 11px;">No token events</td></tr>';
        return;
      }
      
      tbody.innerHTML = timeline.map(e => {
        const ts = new Date(e.timestamp).toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
        return `
          <tr>
            <td class="ts">${ts}</td>
            <td class="ticket">${e.ticket_id}</td>
            <td class="stage">${e.stage.replace('_', ' ')}</td>
            <td class="tokens">+${formatNumber(e.tokens)}</td>
            <td class="cumulative">${formatNumber(e.cumulative_tokens)}</td>
          </tr>
        `;
      }).join('');
      
      // Auto-scroll handled by debouncedScroll
      debouncedScroll();
    }
    
    // Utility functions
    function formatNumber(n) {
      if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
      if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
      return n.toString();
    }
    
    function formatDuration(ms) {
      if (ms < 1000) return Math.round(ms) + 'ms';
      if (ms < 60000) return (ms / 1000).toFixed(1) + 's';
      const min = Math.floor(ms / 60000);
      const sec = Math.floor((ms % 60000) / 1000);
      return `${min}:${sec.toString().padStart(2, '0')}`;
    }
    
    // Initialize
    connect();
    
    // Auto-scroll toggle
    document.getElementById('autoScrollToggle').addEventListener('change', (e) => {
      state.autoScroll = e.target.checked;
    });
    
    // Initialize chart on load
    window.addEventListener('load', () => {
      setTimeout(() => {
        initChart();
        drawChart();
      }, 100);
    });
    window.addEventListener('resize', () => {
      chartInitialized = false;
      initChart();
      drawChart();
    });
    
    // Fetch initial state
    fetch('/api/state')
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          state.metrics = data.metrics || state.metrics;
          state.activeAnalyses = data.active_analyses || {};
          state.completedAnalyses = data.completed_analyses || [];
          updateUI();
        }
      })
      .catch(err => console.error('Failed to fetch state:', err));
  </script>
</body>
</html>'''


# ============================================================================
# HTTP Request Handler
# ============================================================================

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            self._serve_html()
        elif path == '/events':
            self._serve_sse()
        elif path == '/api/state':
            self._serve_state()
        else:
            self._serve_404()
    
    def _serve_html(self):
        """Serve dashboard HTML."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        # Replace domain placeholder with actual domain name
        html = DASHBOARD_HTML.replace('{domain_display_name}', _domain_name)
        self.wfile.write(html.encode('utf-8'))
    
    def _serve_sse(self):
        """Serve Server-Sent Events stream."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Send initial state
        state_data = _state.get_state()
        self._send_event('state', state_data)
        
        # Keep connection alive and send events
        try:
            while True:
                try:
                    # Check for events (non-blocking with timeout)
                    event = _state.events.get(timeout=1.0)
                    self._send_event(event['type'], event['data'])
                except queue.Empty:
                    # Send heartbeat
                    self._send_event('heartbeat', {'time': time.time()})
        except (BrokenPipeError, ConnectionResetError):
            pass
    
    def _send_event(self, event_type: str, data: Dict):
        """Send SSE event."""
        try:
            message = f"data: {json.dumps({'type': event_type, 'data': data, 'timestamp': datetime.now().isoformat()})}\n\n"
            self.wfile.write(message.encode('utf-8'))
            self.wfile.flush()
        except:
            pass
    
    def _serve_state(self):
        """Serve current state as JSON."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        
        state_data = _state.get_state()
        state_data['success'] = True
        self.wfile.write(json.dumps(state_data).encode('utf-8'))
    
    def _serve_404(self):
        """Serve 404."""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')


# ============================================================================
# Threading HTTP Server
# ============================================================================

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP server that handles each request in a separate thread."""
    daemon_threads = True


# ============================================================================
# Dashboard Server
# ============================================================================

class RCADashboard:
    """
    RCA Real-Time Dashboard Server.
    
    Usage:
        dashboard = RCADashboard(port=5050)
        dashboard.start()  # Opens browser
        
        # Or use environment variables:
        # DASHBOARD_PORT=5050
        # DASHBOARD_HOST=localhost
        # DASHBOARD_AUTO_OPEN=true
        
        # Later...
        dashboard.stop()
    """
    
    # Class-level tracking for analysis throttling
    _last_analysis_start: float = 0
    _analysis_lock = threading.Lock()
    ANALYSIS_GAP_SECONDS: float = 2.0  # Minimum gap between analyses
    
    def __init__(self, port: int = None, host: str = None):
        # Read from environment variables with sensible defaults
        self.port = port or int(os.environ.get('DASHBOARD_PORT', 5050))
        self.host = host or os.environ.get('DASHBOARD_HOST', 'localhost')
        self.server: Optional[ThreadingHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self._running = False
    
    def start(self, open_browser: bool = None):
        """Start dashboard server."""
        if self._running:
            print(f"Dashboard already running at http://{self.host}:{self.port}")
            return
        
        # Read auto-open from env if not specified
        if open_browser is None:
            open_browser = os.environ.get('DASHBOARD_AUTO_OPEN', 'true').lower() in ('true', '1', 'yes')
        
        self.server = ThreadingHTTPServer((self.host, self.port), DashboardHandler)
        self._running = True
        
        # Start server in background thread
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        url = f"http://{self.host}:{self.port}"
        print(f"\n{'='*60}")
        print(f"  RCA MONITORING DASHBOARD")
        print(f"{'='*60}")
        print(f"  Server running at: {url}")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*60}\n")
        
        if open_browser:
            webbrowser.open(url)
    
    def _run_server(self):
        """Run server loop."""
        try:
            self.server.serve_forever()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self._running = False
    
    def stop(self):
        """Stop dashboard server."""
        if self.server:
            self.server.shutdown()
            self._running = False
            print("Dashboard stopped")
    
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
    
    # Convenience methods to emit events
    def start_analysis(self, ticket_id: str, defect_data: Dict = None):
        """Track new analysis start with throttling."""
        # Ensure minimum gap between analyses
        with RCADashboard._analysis_lock:
            now = time.time()
            elapsed = now - RCADashboard._last_analysis_start
            if elapsed < RCADashboard.ANALYSIS_GAP_SECONDS:
                wait_time = RCADashboard.ANALYSIS_GAP_SECONDS - elapsed
                print(f"      [Throttle] Waiting {wait_time:.1f}s before starting {ticket_id}...")
                time.sleep(wait_time)
            RCADashboard._last_analysis_start = time.time()
        
        defect_data = defect_data or {}
        _state.active_analyses[ticket_id] = {
            'ticket_id': ticket_id,
            'summary': defect_data.get('summary', '')[:100],
            'component': defect_data.get('component', 'Unknown'),
            'priority': defect_data.get('priority', 'Medium'),
            'status': 'running',
            'stages': {},
            'total_tokens': 0,
            'start_time': time.time()
        }
        _state.add_event('analysis_started', {
            'ticket_id': ticket_id,
            'summary': defect_data.get('summary', ''),
            'component': defect_data.get('component', ''),
            'priority': defect_data.get('priority', '')
        })
    
    def update_stage(self, ticket_id: str, stage: str, status: str):
        """Update stage status."""
        if ticket_id in _state.active_analyses:
            analysis = _state.active_analyses[ticket_id]
            if stage not in analysis['stages']:
                analysis['stages'][stage] = {'status': 'pending', 'tokens': 0, 'start_time': None}
            
            analysis['stages'][stage]['status'] = status
            analysis['current_stage'] = stage
            
            if status == 'running':
                analysis['stages'][stage]['start_time'] = time.time()
            elif status == 'completed' and analysis['stages'][stage].get('start_time'):
                analysis['stages'][stage]['duration_ms'] = (time.time() - analysis['stages'][stage]['start_time']) * 1000
        
        _state.add_event('stage_updated', {
            'ticket_id': ticket_id,
            'stage': stage,
            'status': status
        })
    
    def add_tokens(self, ticket_id: str, stage: str, input_tokens: int, output_tokens: int):
        """Add token consumption."""
        total = input_tokens + output_tokens
        cost_eur = total * 0.000037  # Rough estimate
        
        if ticket_id in _state.active_analyses:
            analysis = _state.active_analyses[ticket_id]
            analysis['total_tokens'] = analysis.get('total_tokens', 0) + total
            if stage in analysis['stages']:
                analysis['stages'][stage]['tokens'] = analysis['stages'][stage].get('tokens', 0) + total
        
        _state.metrics['total_tokens'] = _state.metrics.get('total_tokens', 0) + total
        _state.metrics['total_cost_eur'] = _state.metrics.get('total_cost_eur', 0) + cost_eur
        
        # Add to token timeline
        _state.add_token_event(ticket_id, stage, total, cost_eur)
        
        _state.add_event('tokens_added', {
            'ticket_id': ticket_id,
            'stage': stage,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total,
            'cost_eur': cost_eur,
            'cumulative_tokens': _state.active_analyses.get(ticket_id, {}).get('total_tokens', 0)
        })
    
    def update_confidence(self, ticket_id: str, confidence: float, domain: str = None):
        """Update analysis confidence."""
        if ticket_id in _state.active_analyses:
            _state.active_analyses[ticket_id]['confidence'] = confidence
            if domain:
                _state.active_analyses[ticket_id]['domain'] = domain
        
        _state.add_event('results_updated', {
            'ticket_id': ticket_id,
            'confidence': confidence,
            'domain': domain
        })
    
    def complete_analysis(self, ticket_id: str, success: bool = True):
        """Mark analysis as complete."""
        if ticket_id in _state.active_analyses:
            analysis = _state.active_analyses[ticket_id]
            analysis['status'] = 'completed' if success else 'failed'
            analysis['end_time'] = time.time()
            analysis['duration_ms'] = (analysis['end_time'] - analysis['start_time']) * 1000
            
            _state.completed_analyses.insert(0, analysis.copy())
            del _state.active_analyses[ticket_id]
            _state.metrics['total_tickets'] = _state.metrics.get('total_tickets', 0) + 1
        
        _state.add_event('analysis_completed', {
            'ticket_id': ticket_id,
            'success': success,
            'duration_ms': _state.completed_analyses[0].get('duration_ms', 0) if _state.completed_analyses else 0
        })


# ============================================================================
# Main - Standalone test
# ============================================================================

def main():
    """Run dashboard with simulated data."""
    dashboard = RCADashboard(port=5050)
    dashboard.start(open_browser=True)
    
    # Simulate an analysis
    import random
    
    def simulate_analysis():
        time.sleep(2)
        
        ticket_id = f"TEST-{random.randint(1000, 9999)}"
        dashboard.start_analysis(ticket_id, {
            'summary': '[USB] Source switch from FM to USB takes more than 200ms',
            'component': 'Media',
            'priority': 'High'
        })
        
        stages = [
            ('defect_loading', 0.5, 0, 0),
            ('dlt_analysis', 1.0, 800, 200),
            ('source_mapping', 0.8, 500, 100),
            ('historical_match', 0.6, 1200, 300),
            ('llm_analysis', 2.0, 3000, 1500),
            ('report_generation', 0.5, 200, 100),
        ]
        
        for stage, duration, input_tok, output_tok in stages:
            dashboard.update_stage(ticket_id, stage, 'running')
            time.sleep(duration * 0.5)
            
            if input_tok > 0:
                dashboard.add_tokens(ticket_id, stage, input_tok, output_tok)
            
            time.sleep(duration * 0.5)
            dashboard.update_stage(ticket_id, stage, 'completed')
        
        dashboard.update_confidence(ticket_id, 0.87, 'Media')
        time.sleep(0.5)
        dashboard.complete_analysis(ticket_id, success=True)
    
    # Start simulation thread
    sim_thread = threading.Thread(target=simulate_analysis, daemon=True)
    sim_thread.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        dashboard.stop()


if __name__ == '__main__':
    main()
