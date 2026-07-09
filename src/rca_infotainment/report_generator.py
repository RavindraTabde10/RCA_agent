"""
Report Generator - Generate RCA reports in Markdown and HTML formats

Features:
- Comprehensive Markdown reports
- Styled HTML reports with CSS
- Duplicate/related defect sections
- Evidence and code snippets
- Team assignment recommendations
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class ReportGenerator:
    """
    Generates RCA reports in multiple formats
    
    Supports:
    - Markdown (.md) - for JIRA, GitHub, documentation
    - HTML (.html) - for web viewing, email, presentations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Report Generator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def generate_markdown(self, report_data: Dict[str, Any]) -> str:
        """
        Generate Markdown report
        
        Args:
            report_data: Complete RCA data
            
        Returns:
            Markdown content string
        """
        defect_id = report_data.get("defect_id", "Unknown")
        defect = report_data.get("defect_data", {})
        dlt = report_data.get("dlt_analysis", {})
        source = report_data.get("source_mapping", {})
        historical = report_data.get("historical_matches", [])
        llm = report_data.get("llm_analysis", {})
        duplicate = report_data.get("duplicate_info", {})
        timestamp = report_data.get("timestamp", datetime.now().isoformat())
        
        lines = []
        
        # Header
        lines.append(f"# Root Cause Analysis Report: {defect_id}")
        lines.append("")
        lines.append(f"**Generated:** {timestamp}")
        lines.append(f"**Status:** {'⚠️ POTENTIAL DUPLICATE' if duplicate.get('is_duplicate') else '✅ Analyzed'}")
        lines.append("")
        
        # Duplicate Warning
        if duplicate.get("is_duplicate"):
            lines.append("---")
            lines.append("## ⚠️ Duplicate Detection")
            lines.append("")
            lines.append(f"This defect is **{duplicate['similarity_score']:.0%}** similar to **{duplicate['duplicate_of']}**")
            lines.append("")
            lines.append("> **Recommendation:** Review and link as duplicate if confirmed.")
            lines.append("")
        
        # Defect Summary
        lines.append("---")
        lines.append("## 📋 Defect Summary")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **ID** | {defect_id} |")
        lines.append(f"| **Summary** | {defect.get('summary', 'N/A')} |")
        lines.append(f"| **Component** | {defect.get('component', 'N/A')} |")
        lines.append(f"| **Priority** | {defect.get('priority', 'N/A')} |")
        lines.append(f"| **Status** | {defect.get('status', 'N/A')} |")
        lines.append("")
        
        if defect.get("description"):
            lines.append("### Description")
            lines.append(defect["description"])
            lines.append("")
        
        # Root Cause Analysis
        lines.append("---")
        lines.append("## 🔍 Root Cause Analysis")
        lines.append("")
        lines.append(f"**Confidence:** {llm.get('confidence', 0):.0%}")
        lines.append("")
        lines.append("### Root Cause")
        lines.append(llm.get("root_cause", "Unable to determine root cause"))
        lines.append("")
        
        # Fix Recommendation
        lines.append("### 🔧 Fix Recommendation")
        lines.append(llm.get("fix_recommendation", "See evidence section for details"))
        lines.append("")
        
        # Evidence
        if llm.get("evidence"):
            lines.append("### 📊 Evidence")
            lines.append("")
            for evidence in llm["evidence"]:
                lines.append(f"- {evidence}")
            lines.append("")
        
        # DLT Log Analysis
        lines.append("---")
        lines.append("## 📝 DLT Log Analysis")
        lines.append("")
        
        summary = dlt.get("summary", {})
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Total Errors** | {summary.get('error_count', 0)} |")
        lines.append(f"| **Total Warnings** | {summary.get('warning_count', 0)} |")
        lines.append(f"| **Components** | {summary.get('component_count', 0)} |")
        lines.append("")
        
        if dlt.get("components"):
            lines.append(f"**Affected Components:** {', '.join(dlt['components'])}")
            lines.append("")
        
        if dlt.get("patterns"):
            lines.append("### Detected Patterns")
            for pattern in dlt["patterns"][:5]:
                lines.append(f"- **{pattern.get('type', 'unknown')}**: {pattern.get('message', '')[:60]}...")
            lines.append("")
        
        if dlt.get("errors"):
            lines.append("### Error Log Entries")
            lines.append("```")
            for error in dlt["errors"][:10]:
                lines.append(f"[{error.get('component', '?')}] {error.get('message', '')[:80]}")
            lines.append("```")
            lines.append("")
        
        # Source Code Mapping
        lines.append("---")
        lines.append("## 📁 Source Code Mapping")
        lines.append("")
        
        if source.get("mapped_files"):
            lines.append("| File | Component | Confidence | Reason |")
            lines.append("|------|-----------|------------|--------|")
            for f in source["mapped_files"][:10]:
                lines.append(f"| `{f.get('file', 'N/A')}` | {f.get('component', 'N/A')} | {f.get('confidence', 0):.0%} | {f.get('reason', '')} |")
            lines.append("")
        else:
            lines.append("No source files mapped.")
            lines.append("")
        
        # Historical Defects
        if historical:
            lines.append("---")
            lines.append("## 📚 Similar Historical Defects")
            lines.append("")
            lines.append("| Defect | Similarity | Component | Root Cause |")
            lines.append("|--------|------------|-----------|------------|")
            for h in historical[:5]:
                root_cause = h.get('root_cause', 'N/A')[:50]
                if len(h.get('root_cause', '')) > 50:
                    root_cause += '...'
                lines.append(f"| {h.get('defect_id', 'N/A')} | {h.get('similarity_score', 0):.0%} | {h.get('component', 'N/A')} | {root_cause} |")
            lines.append("")
        
        # Preventive Measures
        if llm.get("preventive_measures"):
            lines.append("---")
            lines.append("## 🛡️ Preventive Measures")
            lines.append("")
            for measure in llm["preventive_measures"]:
                lines.append(f"- {measure}")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("*This report was generated by the RCA Agent. Please review and validate findings.*")
        
        return "\n".join(lines)
    
    def generate_html(self, report_data: Dict[str, Any]) -> str:
        """
        Generate styled HTML report
        
        Args:
            report_data: Complete RCA data
            
        Returns:
            HTML content string
        """
        defect_id = report_data.get("defect_id", "Unknown")
        defect = report_data.get("defect_data", {})
        dlt = report_data.get("dlt_analysis", {})
        source = report_data.get("source_mapping", {})
        historical = report_data.get("historical_matches", [])
        llm = report_data.get("llm_analysis", {})
        duplicate = report_data.get("duplicate_info", {})
        timestamp = report_data.get("timestamp", datetime.now().isoformat())
        
        # CSS Styles
        css = self._get_css_styles()
        
        # Build HTML
        html_parts = []
        
        html_parts.append(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RCA Report - {defect_id}</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🔍 Root Cause Analysis Report</h1>
            <h2>{defect_id}</h2>
            <p class="timestamp">Generated: {timestamp}</p>
        </header>
""")
        
        # Duplicate Warning Banner
        if duplicate.get("is_duplicate"):
            html_parts.append(f"""
        <div class="alert alert-warning">
            <h3>⚠️ Potential Duplicate Detected</h3>
            <p>This defect is <strong>{duplicate['similarity_score']:.0%}</strong> similar to 
               <strong>{duplicate['duplicate_of']}</strong></p>
            <p>Recommendation: Review and link as duplicate if confirmed.</p>
        </div>
""")
        
        # Confidence Score Card
        confidence = llm.get("confidence", 0)
        confidence_class = "high" if confidence >= 0.7 else "medium" if confidence >= 0.5 else "low"
        html_parts.append(f"""
        <div class="card confidence-card {confidence_class}">
            <h3>Analysis Confidence</h3>
            <div class="confidence-score">{confidence:.0%}</div>
        </div>
""")
        
        # Defect Summary
        html_parts.append(f"""
        <section class="card">
            <h3>📋 Defect Summary</h3>
            <table class="info-table">
                <tr><th>ID</th><td>{defect_id}</td></tr>
                <tr><th>Summary</th><td>{defect.get('summary', 'N/A')}</td></tr>
                <tr><th>Component</th><td><span class="badge">{defect.get('component', 'N/A')}</span></td></tr>
                <tr><th>Priority</th><td>{defect.get('priority', 'N/A')}</td></tr>
                <tr><th>Status</th><td>{defect.get('status', 'N/A')}</td></tr>
            </table>
        </section>
""")
        
        # Root Cause
        root_cause = llm.get("root_cause", "Unable to determine").replace('\n', '<br>')
        html_parts.append(f"""
        <section class="card highlight">
            <h3>🔍 Root Cause</h3>
            <p class="root-cause">{root_cause}</p>
        </section>
""")
        
        # Fix Recommendation
        fix_rec = llm.get("fix_recommendation", "See evidence section").replace('\n', '<br>')
        html_parts.append(f"""
        <section class="card">
            <h3>🔧 Fix Recommendation</h3>
            <p>{fix_rec}</p>
        </section>
""")
        
        # Evidence
        if llm.get("evidence"):
            evidence_html = "\n".join([f"<li>{e}</li>" for e in llm["evidence"]])
            html_parts.append(f"""
        <section class="card">
            <h3>📊 Evidence</h3>
            <ul class="evidence-list">
                {evidence_html}
            </ul>
        </section>
""")
        
        # DLT Analysis
        summary = dlt.get("summary", {})
        errors_html = ""
        if dlt.get("errors"):
            error_lines = [f'<div class="log-line error">[{e.get("component", "?")}] {e.get("message", "")[:80]}</div>' 
                          for e in dlt["errors"][:10]]
            errors_html = "\n".join(error_lines)
        
        html_parts.append(f"""
        <section class="card">
            <h3>📝 DLT Log Analysis</h3>
            <div class="stats-row">
                <div class="stat">
                    <span class="stat-number">{summary.get('error_count', 0)}</span>
                    <span class="stat-label">Errors</span>
                </div>
                <div class="stat">
                    <span class="stat-number">{summary.get('warning_count', 0)}</span>
                    <span class="stat-label">Warnings</span>
                </div>
                <div class="stat">
                    <span class="stat-number">{summary.get('component_count', 0)}</span>
                    <span class="stat-label">Components</span>
                </div>
            </div>
            <div class="log-box">
                {errors_html}
            </div>
        </section>
""")
        
        # Source Files
        if source.get("mapped_files"):
            files_rows = ""
            for f in source["mapped_files"][:10]:
                conf = f.get('confidence', 0)
                conf_class = "high" if conf >= 0.8 else "medium" if conf >= 0.6 else "low"
                files_rows += f"""
                <tr>
                    <td><code>{f.get('file', 'N/A')}</code></td>
                    <td><span class="badge">{f.get('component', 'N/A')}</span></td>
                    <td><span class="confidence-badge {conf_class}">{conf:.0%}</span></td>
                </tr>"""
            
            html_parts.append(f"""
        <section class="card">
            <h3>📁 Affected Source Files</h3>
            <table class="data-table">
                <thead>
                    <tr><th>File</th><th>Component</th><th>Confidence</th></tr>
                </thead>
                <tbody>
                    {files_rows}
                </tbody>
            </table>
        </section>
""")
        
        # Historical Defects
        if historical:
            hist_rows = ""
            for h in historical[:5]:
                sim = h.get('similarity_score', 0)
                sim_class = "high" if sim >= 0.9 else "medium" if sim >= 0.7 else "low"
                hist_rows += f"""
                <tr>
                    <td><strong>{h.get('defect_id', 'N/A')}</strong></td>
                    <td><span class="confidence-badge {sim_class}">{sim:.0%}</span></td>
                    <td>{h.get('component', 'N/A')}</td>
                    <td>{h.get('root_cause', 'N/A')[:60]}...</td>
                </tr>"""
            
            html_parts.append(f"""
        <section class="card">
            <h3>📚 Similar Historical Defects</h3>
            <table class="data-table">
                <thead>
                    <tr><th>Defect</th><th>Similarity</th><th>Component</th><th>Root Cause</th></tr>
                </thead>
                <tbody>
                    {hist_rows}
                </tbody>
            </table>
        </section>
""")
        
        # Preventive Measures
        if llm.get("preventive_measures"):
            measures_html = "\n".join([f"<li>{m}</li>" for m in llm["preventive_measures"]])
            html_parts.append(f"""
        <section class="card">
            <h3>🛡️ Preventive Measures</h3>
            <ul>
                {measures_html}
            </ul>
        </section>
""")
        
        # Footer
        html_parts.append("""
        <footer class="footer">
            <p>Generated by RCA Agent • Please review and validate findings</p>
        </footer>
    </div>
</body>
</html>
""")
        
        return "".join(html_parts)
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header h2 {
            color: #667eea;
            font-size: 36px;
            font-weight: 700;
        }
        
        .timestamp {
            color: #666;
            margin-top: 10px;
        }
        
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .card h3 {
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .card.highlight {
            border-left: 4px solid #667eea;
        }
        
        .alert {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        
        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
        }
        
        .alert-warning h3 {
            color: #856404;
            border: none;
        }
        
        .confidence-card {
            text-align: center;
            padding: 30px;
        }
        
        .confidence-card.high { border-top: 4px solid #28a745; }
        .confidence-card.medium { border-top: 4px solid #ffc107; }
        .confidence-card.low { border-top: 4px solid #dc3545; }
        
        .confidence-score {
            font-size: 48px;
            font-weight: 700;
            color: #333;
        }
        
        .info-table {
            width: 100%;
        }
        
        .info-table th {
            text-align: left;
            padding: 10px;
            width: 150px;
            color: #666;
        }
        
        .info-table td {
            padding: 10px;
        }
        
        .badge {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        .confidence-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .confidence-badge.high { background: #d4edda; color: #155724; }
        .confidence-badge.medium { background: #fff3cd; color: #856404; }
        .confidence-badge.low { background: #f8d7da; color: #721c24; }
        
        .root-cause {
            font-size: 18px;
            line-height: 1.6;
            color: #333;
        }
        
        .stats-row {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat {
            flex: 1;
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .stat-number {
            display: block;
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        
        .log-box {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .log-line {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            padding: 4px 0;
            border-bottom: 1px solid #333;
        }
        
        .log-line.error {
            color: #ff6b6b;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        .data-table code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .evidence-list li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: white;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .stats-row {
                flex-direction: column;
            }
        }
        """
