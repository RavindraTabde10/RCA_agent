"""
HTML Report Generator for RCA Pre-Analysis Workflow.

Generates an interactive single-page HTML report from the RCA analysis results.
The HTML report includes:
 - Sidebar navigation for quick section access
 - Overview summary with key findings
 - Individual analysis sections (DLT Analysis, Root Cause, Historical Matches, etc.)
 - Workflow step timing table
 - Collapsible raw content sections
 - Code fix preview with before/after diff

All styles and scripts are embedded (no external dependencies).
"""

import html
import re
from datetime import datetime
from typing import Dict, Any, List, Optional


# ============================================================================
# Public API
# ============================================================================

def generate_standalone_html_report(
    jira_key: str,
    title: str,
    icon: str,
    markdown_content: str,
    badge: str = None
) -> str:
    """
    Generate a standalone single-section HTML report.
    
    Used for individual artifact reports (DLT Analysis, Log/Trace, etc.)
    so that each report can be opened independently in a browser.
    
    Args:
        jira_key: JIRA key (e.g., SAM1-2001)
        title: Report title shown in header and browser tab
        icon: Icon emoji for the header
        markdown_content: The markdown content to render
        badge: Optional extra badge text in the header (e.g., domain name)
    
    Returns:
        Complete HTML document as a string
    """
    timestamp = datetime.now().isoformat()
    body_html = markdown_to_html(markdown_content)
    
    badge_html = f'<span class="badge domain">{escape_html(badge)}</span>' if badge else ''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(title)} — {escape_html(jira_key)}</title>
  {get_standalone_styles()}
</head>
<body>
  <header class="top-bar">
    <div class="header-info">
      <span class="header-icon">{icon}</span>
      <h1>{escape_html(title)}</h1>
      <span class="badge primary">{escape_html(jira_key)}</span>
      {badge_html}
    </div>
    <span class="timestamp">Generated {escape_html(timestamp.split('T')[0])}</span>
  </header>

  <main class="content">
    <div class="markdown-body">{body_html}</div>
  </main>

  <footer class="footer">
    <span>RCA Report — {escape_html(jira_key)}</span>
  </footer>

  {get_standalone_scripts()}
</body>
</html>'''


def generate_rca_html_report(
    rca_result: Dict[str, Any],
    defect_data: Dict[str, Any] = None
) -> str:
    """
    Generate the main interactive HTML report from RCA analysis results.
    
    All report content is embedded inline so the file is fully self-contained
    and shareable as a single file. Detailed sections are rendered with 
    sidebar navigation.
    
    Args:
        rca_result: Full RCA analysis result from RCAEngine.analyze_defect()
        defect_data: Optional defect data for additional context
        
    Returns:
        Complete HTML document as a string
    """
    defect_id = rca_result.get("defect_id", "Unknown")
    stages = rca_result.get("stages", {})
    
    # Extract analysis data
    dlt_analysis = stages.get("dlt_analysis", {}).get("data", {})
    llm_analysis = stages.get("llm_analysis", {}).get("data", {})
    historical_matches = stages.get("historical_match", {}).get("data", {}).get("matches", [])
    source_mapping = stages.get("source_mapping", {}).get("data", {})
    
    # Build sections
    inline_sections = build_inline_sections(rca_result, defect_data)
    
    timestamp = datetime.now().isoformat()
    total_duration = rca_result.get("duration_seconds", 0)
    domain = llm_analysis.get("domain", dlt_analysis.get("domain", "Unknown"))
    confidence = llm_analysis.get("confidence", 0)
    
    # Sidebar navigation
    nav_links = "\n      ".join([
        f'<a href="#{s["id"]}" class="nav-link{" active" if s["id"] == "overview" else ""}" data-section="{s["id"]}"><span class="nav-icon">{s["icon"]}</span>{escape_html(s["title"])}</a>'
        for s in inline_sections
    ])
    
    # Render sections
    sections_html = "\n".join([
        render_section(s, s["id"] == "overview") for s in inline_sections
    ])
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RCA Report — {escape_html(defect_id)}</title>
  {get_styles()}
</head>
<body>
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="logo">RCA</div>
      <h2>RCA Report</h2>
    </div>
    <div class="nav-links">
      {nav_links}
    </div>
    <div class="sidebar-footer">
      <span class="timestamp">Generated {escape_html(timestamp.split('T')[0])}</span>
    </div>
  </nav>

  <main class="content">
    <header class="top-bar">
      <button class="menu-toggle" onclick="toggleSidebar()" aria-label="Toggle sidebar">☰</button>
      <div class="header-info">
        <h1>{escape_html(defect_id)}</h1>
        <span class="badge domain">{escape_html(domain)}</span>
        <span class="badge confidence">🎯 {confidence:.0%} confidence</span>
        <span class="badge duration">⏱ {format_duration(total_duration)}</span>
      </div>
    </header>

    {sections_html}
  </main>

  {get_scripts()}
</body>
</html>'''


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


# ============================================================================
# Section Building
# ============================================================================

def build_inline_sections(
    rca_result: Dict[str, Any],
    defect_data: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Build sections rendered inline on the main landing page."""
    sections = []
    
    sections.append(build_overview_section(rca_result, defect_data))
    sections.append(build_root_cause_section(rca_result))
    sections.append(build_dlt_analysis_section(rca_result))
    sections.append(build_historical_section(rca_result))
    sections.append(build_source_mapping_section(rca_result))
    sections.append(build_code_fix_section(rca_result))
    sections.append(build_workflow_steps_section(rca_result))
    
    # Filter out empty sections
    return [s for s in sections if s.get("content")]


def build_overview_section(
    rca_result: Dict[str, Any],
    defect_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Build overview section with key metrics."""
    defect_id = rca_result.get("defect_id", "Unknown")
    stages = rca_result.get("stages", {})
    llm_analysis = stages.get("llm_analysis", {}).get("data", {})
    dlt_analysis = stages.get("dlt_analysis", {}).get("data", {})
    historical = stages.get("historical_match", {}).get("data", {}).get("matches", [])
    
    domain = llm_analysis.get("domain", dlt_analysis.get("domain", "Unknown"))
    confidence = llm_analysis.get("confidence", 0)
    root_cause = llm_analysis.get("root_cause", "N/A")
    total_duration = rca_result.get("duration_seconds", 0)
    
    defect_data = defect_data or {}
    summary = defect_data.get("summary", llm_analysis.get("summary", "N/A"))
    priority = defect_data.get("priority", "Unknown")
    component = defect_data.get("component", dlt_analysis.get("component", "Unknown"))
    
    # Key metrics cards
    cards = [
        {"label": "JIRA Key", "value": defect_id, "cls": "primary"},
        {"label": "Domain", "value": domain, "cls": "info"},
        {"label": "Component", "value": component, "cls": "neutral"},
        {"label": "Priority", "value": priority, "cls": "warning" if "High" in priority else "neutral"},
        {"label": "Confidence", "value": f"{confidence:.0%}", "cls": "success" if confidence >= 0.7 else "warning"},
        {"label": "Duration", "value": format_duration(total_duration), "cls": "neutral"},
        {"label": "Historical Matches", "value": str(len(historical)), "cls": "info"},
        {"label": "Errors Found", "value": str(len(dlt_analysis.get("errors", []))), "cls": "error" if dlt_analysis.get("errors") else "success"},
    ]
    
    cards_html = "".join([
        f'<div class="card card-{c["cls"]}"><span class="card-label">{escape_html(c["label"])}</span><span class="card-value">{escape_html(str(c["value"]))}</span></div>'
        for c in cards
    ])
    
    # Analysis flags
    flags = [
        {"label": "DLT Analysis", "available": bool(dlt_analysis)},
        {"label": "Root Cause", "available": bool(root_cause and root_cause != "N/A")},
        {"label": "Historical Match", "available": len(historical) > 0},
        {"label": "Source Mapping", "available": bool(stages.get("source_mapping", {}).get("data", {}).get("mapped_files"))},
        {"label": "Code Fix", "available": bool(llm_analysis.get("code_fixes"))},
    ]
    
    flags_html = "".join([
        f'<span class="flag {"flag-on" if f["available"] else "flag-off"}">{"✓" if f["available"] else "✗"} {escape_html(f["label"])}</span>'
        for f in flags
    ])
    
    content = f'''
    <div class="cards-grid">{cards_html}</div>
    <h3>Summary</h3>
    <p class="jira-summary">{escape_html(summary[:500] if summary else "N/A")}</p>
    <h3>Analysis Components</h3>
    <div class="flags-row">{flags_html}</div>
    <h3>Root Cause (Brief)</h3>
    <p class="root-cause-brief">{escape_html(root_cause[:300] if root_cause else "N/A")}...</p>
    '''
    
    return {"id": "overview", "title": "Overview", "icon": "📊", "content": content}


def build_root_cause_section(rca_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build root cause analysis section."""
    stages = rca_result.get("stages", {})
    llm_analysis = stages.get("llm_analysis", {}).get("data", {})
    
    root_cause = llm_analysis.get("root_cause", "")
    evidence = llm_analysis.get("evidence", [])
    fix_recommendation = llm_analysis.get("fix_recommendation", "")
    affected_files = llm_analysis.get("affected_files", [])
    confidence = llm_analysis.get("confidence", 0)
    
    if not root_cause:
        return {"id": "root-cause", "title": "Root Cause", "icon": "🔍", "content": ""}
    
    # Evidence list
    evidence_html = ""
    if evidence:
        evidence_items = "".join([f"<li>{escape_html(str(e)[:200])}</li>" for e in evidence[:10]])
        evidence_html = f"<h3>Evidence</h3><ul>{evidence_items}</ul>"
    
    # Affected files
    files_html = ""
    if affected_files:
        files_items = "".join([f"<li><code>{escape_html(f)}</code></li>" for f in affected_files[:10]])
        files_html = f"<h3>Affected Source Files</h3><ul>{files_items}</ul>"
    
    # Fix recommendation - use markdown_to_html to properly format code blocks, lists, etc.
    fix_html = ""
    if fix_recommendation:
        fix_content = markdown_to_html(fix_recommendation)
        fix_html = f"<h3>Recommended Fix</h3><div class='fix-recommendation'>{fix_content}</div>"
    
    content = f'''
    <div class="confidence-bar">
        <span class="confidence-label">Confidence: {confidence:.0%}</span>
        <div class="confidence-track"><div class="confidence-fill" style="width: {confidence*100}%"></div></div>
    </div>
    <h3>Root Cause</h3>
    <div class="root-cause-box">{markdown_to_html(root_cause)}</div>
    {evidence_html}
    {files_html}
    {fix_html}
    '''
    
    return {"id": "root-cause", "title": "Root Cause Analysis", "icon": "🔍", "content": content}


def build_dlt_analysis_section(rca_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build DLT log analysis section."""
    stages = rca_result.get("stages", {})
    dlt_analysis = stages.get("dlt_analysis", {}).get("data", {})
    
    if not dlt_analysis:
        return {"id": "dlt-analysis", "title": "DLT Analysis", "icon": "📋", "content": ""}
    
    errors = dlt_analysis.get("errors", [])
    warnings = dlt_analysis.get("warnings", [])
    components = dlt_analysis.get("components", [])
    timeline = dlt_analysis.get("timeline", [])
    
    # Errors table
    errors_html = ""
    if errors:
        error_rows = "".join([
            f"<tr><td>{escape_html(str(e.get('timestamp', 'N/A')) if isinstance(e, dict) else 'N/A')}</td><td>{escape_html(str(e.get('message', str(e)) if isinstance(e, dict) else str(e))[:150])}</td></tr>"
            for e in errors[:20]
        ])
        errors_html = f'''
        <h3>🔴 Errors Found ({len(errors)})</h3>
        <table class="md-table">
            <thead><tr><th>Timestamp</th><th>Message</th></tr></thead>
            <tbody>{error_rows}</tbody>
        </table>
        '''
    
    # Warnings
    warnings_html = ""
    if warnings:
        warning_rows = "".join([
            f"<tr><td>{escape_html(str(w)[:200])}</td></tr>"
            for w in warnings[:10]
        ])
        warnings_html = f'''
        <h3>⚠️ Warnings ({len(warnings)})</h3>
        <table class="md-table">
            <thead><tr><th>Warning</th></tr></thead>
            <tbody>{warning_rows}</tbody>
        </table>
        '''
    
    # Components
    components_html = ""
    if components:
        comp_items = "".join([f'<span class="component-tag">{escape_html(c)}</span>' for c in components[:15]])
        components_html = f"<h3>Affected Components</h3><div class='components-list'>{comp_items}</div>"
    
    content = f'''
    {errors_html}
    {warnings_html}
    {components_html}
    '''
    
    return {"id": "dlt-analysis", "title": "DLT Log Analysis", "icon": "📋", "content": content}


def build_historical_section(rca_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build historical matches section."""
    stages = rca_result.get("stages", {})
    historical_data = stages.get("historical_match", {}).get("data", {})
    matches = historical_data.get("matches", [])
    
    if not matches:
        return {"id": "historical", "title": "Similar Defects", "icon": "🔗", "content": "<p class='empty-notice'>No similar historical defects found.</p>"}
    
    # Build table rows
    rows = "".join([
        f'''<tr>
            <td>{i+1}</td>
            <td><strong>{escape_html(m.get('defect_id', 'N/A'))}</strong></td>
            <td>{m.get('similarity_score', 0):.0%}</td>
            <td>{escape_html(str(m.get('summary', 'N/A'))[:100])}</td>
            <td>{escape_html(str(m.get('root_cause', 'N/A'))[:100])}</td>
        </tr>'''
        for i, m in enumerate(matches[:10])
    ])
    
    content = f'''
    <p>Found <strong>{len(matches)}</strong> similar historical defects.</p>
    <table class="md-table">
        <thead>
            <tr><th>#</th><th>JIRA Key</th><th>Similarity</th><th>Summary</th><th>Root Cause</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    '''
    
    return {"id": "historical", "title": "Similar Defects", "icon": "🔗", "content": content}


def build_source_mapping_section(rca_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build source code mapping section."""
    stages = rca_result.get("stages", {})
    source_data = stages.get("source_mapping", {}).get("data", {})
    mapped_files = source_data.get("mapped_files", [])
    
    if not mapped_files:
        return {"id": "source-mapping", "title": "Source Mapping", "icon": "📁", "content": ""}
    
    rows = "".join([
        f'''<tr>
            <td><code>{escape_html(f.get('file', 'N/A'))}</code></td>
            <td>{escape_html(f.get('reason', 'N/A'))}</td>
            <td>{f.get('confidence', 0):.0%}</td>
        </tr>'''
        for f in mapped_files[:15]
    ])
    
    content = f'''
    <p>Mapped <strong>{len(mapped_files)}</strong> source files to this defect.</p>
    <table class="md-table">
        <thead><tr><th>File</th><th>Reason</th><th>Confidence</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    '''
    
    return {"id": "source-mapping", "title": "Source Mapping", "icon": "📁", "content": content}


def build_code_fix_section(rca_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build code fix preview section with before/after diff."""
    stages = rca_result.get("stages", {})
    llm_analysis = stages.get("llm_analysis", {}).get("data", {})
    code_fixes = llm_analysis.get("code_fixes", [])
    
    if not code_fixes:
        return {"id": "code-fix", "title": "Proposed Fix", "icon": "🔧", "content": ""}
    
    fixes_html = ""
    for idx, fix in enumerate(code_fixes[:5], 1):
        file_path = fix.get("file_path", "Unknown file")
        description = fix.get("description", "Code fix")
        old_content = fix.get("old_content", "")
        new_content = fix.get("new_content", "")
        
        old_html = ""
        if old_content:
            old_display = old_content[:800] + "\n..." if len(old_content) > 800 else old_content
            old_html = f'''
            <div class="code-diff-block diff-remove">
                <div class="diff-header">❌ BEFORE (Remove)</div>
                <pre class="code-block">{escape_html(old_display)}</pre>
            </div>
            '''
        
        new_html = ""
        if new_content:
            new_display = new_content[:800] + "\n..." if len(new_content) > 800 else new_content
            new_html = f'''
            <div class="code-diff-block diff-add">
                <div class="diff-header">✅ AFTER (Add)</div>
                <pre class="code-block">{escape_html(new_display)}</pre>
            </div>
            '''
        
        fixes_html += f'''
        <div class="fix-item">
            <h4>Fix {idx}: <code>{escape_html(file_path)}</code></h4>
            <p class="fix-description">{escape_html(description)}</p>
            <div class="code-diff-container">
                {old_html}
                {new_html}
            </div>
        </div>
        '''
    
    content = f'''
    <p>Generated <strong>{len(code_fixes)}</strong> code fix suggestion(s).</p>
    {fixes_html}
    '''
    
    return {"id": "code-fix", "title": "Proposed Code Fix", "icon": "🔧", "content": content}


def build_workflow_steps_section(rca_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build workflow steps timing section."""
    stages = rca_result.get("stages", {})
    total_duration = rca_result.get("duration_seconds", 0)
    
    if not stages:
        return {"id": "workflow-steps", "title": "Workflow Steps", "icon": "⚙️", "content": ""}
    
    rows = ""
    for step_num, (step_name, step_data) in enumerate(stages.items(), 1):
        status = step_data.get("status", "unknown")
        duration = step_data.get("duration", 0)
        pct = (duration / total_duration * 100) if total_duration > 0 else 0
        
        status_html = '<span class="status-ok">✅ OK</span>' if status == "completed" else '<span class="status-error">⚠️ Error</span>'
        
        rows += f'''
        <tr>
            <td>{step_num}</td>
            <td>{escape_html(step_name.replace('_', ' ').title())}</td>
            <td>{status_html}</td>
            <td>{format_duration(duration)}</td>
            <td><div class="bar-cell"><div class="bar" style="width:{pct:.1f}%"></div><span>{pct:.1f}%</span></div></td>
        </tr>
        '''
    
    content = f'''
    <table class="steps-table">
        <thead><tr><th>#</th><th>Step</th><th>Status</th><th>Duration</th><th>% of Total</th></tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr><td colspan="3"><strong>Total</strong></td><td><strong>{format_duration(total_duration)}</strong></td><td></td></tr></tfoot>
    </table>
    '''
    
    return {"id": "workflow-steps", "title": "Workflow Steps", "icon": "⚙️", "content": content}


def render_section(section: Dict[str, Any], is_active: bool = False) -> str:
    """Render a section to HTML."""
    active_class = " active" if is_active else ""
    return f'''
    <section id="{section['id']}" class="report-section{active_class}">
        <h2><span class="section-icon">{section['icon']}</span> {escape_html(section['title'])}</h2>
        <div class="section-body">{section['content']}</div>
    </section>
    '''


# ============================================================================
# Markdown to HTML Converter
# ============================================================================

def markdown_to_html(md: str) -> str:
    """
    Convert markdown string to HTML. Handles common markdown:
    headings, bold, italic, code blocks, inline code, tables, lists, links.
    """
    if not md:
        return ""
    
    lines = md.split('\n')
    out = []
    in_code_block = False
    in_table = False
    in_list = None  # 'ul' or 'ol'
    
    def close_list():
        nonlocal in_list
        if in_list == 'ul':
            out.append('</ul>')
        elif in_list == 'ol':
            out.append('</ol>')
        in_list = None
    
    def close_table():
        nonlocal in_table
        if in_table:
            out.append('</tbody></table>')
            in_table = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Fenced code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                out.append('</code></pre>')
                in_code_block = False
            else:
                close_list()
                close_table()
                lang = line.strip()[3:].strip()
                lang_attr = f' class="language-{escape_html(lang)}"' if lang else ''
                out.append(f'<pre class="code-block"><code{lang_attr}>')
                in_code_block = True
            i += 1
            continue
        
        if in_code_block:
            out.append(escape_html(line))
            i += 1
            continue
        
        trimmed = line.strip()
        
        # Blank line
        if not trimmed:
            close_list()
            close_table()
            i += 1
            continue
        
        # Horizontal rule
        if re.match(r'^[-*_]{3,}$', trimmed) or re.match(r'^={4,}$', trimmed):
            close_list()
            close_table()
            out.append('<hr>')
            i += 1
            continue
        
        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.*)', trimmed)
        if heading_match:
            close_list()
            close_table()
            level = len(heading_match.group(1))
            out.append(f'<h{level}>{inline_markdown(heading_match.group(2))}</h{level}>')
            i += 1
            continue
        
        # Table rows
        if trimmed.startswith('|') and trimmed.endswith('|'):
            close_list()
            # Separator row
            if re.match(r'^\|[\s:-]+\|', trimmed) and '---' in trimmed:
                i += 1
                continue
            
            if not in_table:
                out.append('<table class="md-table"><thead>')
                cells = split_table_cells(trimmed)
                out.append('<tr>' + ''.join([f'<th>{inline_markdown(c)}</th>' for c in cells]) + '</tr>')
                out.append('</thead><tbody>')
                in_table = True
                # Check if next line is separator
                if i + 1 < len(lines) and re.match(r'^\|[\s:-]+\|', lines[i + 1].strip()):
                    i += 1
                i += 1
                continue
            
            cells = split_table_cells(trimmed)
            out.append('<tr>' + ''.join([f'<td>{inline_markdown(c)}</td>' for c in cells]) + '</tr>')
            i += 1
            continue
        
        # Unordered list
        ul_match = re.match(r'^[-*+]\s+(.*)', trimmed)
        if ul_match:
            close_table()
            if in_list != 'ul':
                close_list()
                out.append('<ul>')
                in_list = 'ul'
            out.append(f'<li>{inline_markdown(ul_match.group(1))}</li>')
            i += 1
            continue
        
        # Ordered list
        ol_match = re.match(r'^\d+\.\s+(.*)', trimmed)
        if ol_match:
            close_table()
            if in_list != 'ol':
                close_list()
                out.append('<ol>')
                in_list = 'ol'
            out.append(f'<li>{inline_markdown(ol_match.group(1))}</li>')
            i += 1
            continue
        
        # Regular paragraph
        close_list()
        close_table()
        out.append(f'<p>{inline_markdown(trimmed)}</p>')
        i += 1
    
    # Close any open blocks
    if in_code_block:
        out.append('</code></pre>')
    close_list()
    close_table()
    
    return '\n'.join(out)


def split_table_cells(row: str) -> List[str]:
    """Split a markdown table row into cells."""
    return [c.strip() for c in row.split('|')[1:-1]]


def inline_markdown(text: str) -> str:
    """Convert inline markdown tokens to HTML."""
    text = escape_html(text)
    
    # Bold + Italic
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # JIRA file references [^filename]
    text = re.sub(r'\[\^([^\]]+)\]', r'<span class="file-ref">📎 \1</span>', text)
    
    return text


# ============================================================================
# HTML Escaping
# ============================================================================

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return html.escape(str(text))


# ============================================================================
# Embedded CSS
# ============================================================================

def get_styles() -> str:
    """Return embedded CSS styles for the main report."""
    return '''<style>
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
    --sidebar-width: 260px;
    --header-height: 60px;
    --radius: 8px;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    display: flex;
    min-height: 100vh;
  }

  /* Sidebar */
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: var(--sidebar-width);
    height: 100vh;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    z-index: 100;
    transition: transform 0.3s ease;
  }
  .sidebar-header {
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid var(--border);
  }
  .sidebar-header .logo {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--accent), var(--success));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 12px;
    color: #fff;
    flex-shrink: 0;
  }
  .sidebar-header h2 {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }
  .nav-links {
    flex: 1;
    overflow-y: auto;
    padding: 12px 0;
  }
  .nav-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    transition: all 0.15s ease;
    border-left: 3px solid transparent;
  }
  .nav-link:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  .nav-link.active {
    color: var(--accent-light);
    background: rgba(108, 140, 255, 0.08);
    border-left-color: var(--accent);
  }
  .nav-icon { font-size: 16px; }
  .sidebar-footer {
    padding: 16px 20px;
    border-top: 1px solid var(--border);
  }
  .timestamp {
    font-size: 12px;
    color: var(--text-muted);
  }

  /* Main content */
  .content {
    margin-left: var(--sidebar-width);
    flex: 1;
    min-width: 0;
  }
  .top-bar {
    position: sticky;
    top: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 32px;
    height: var(--header-height);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(10px);
  }
  .menu-toggle {
    display: none;
    background: none;
    border: 1px solid var(--border);
    color: var(--text-primary);
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
  }
  .header-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .header-info h1 {
    font-size: 20px;
    font-weight: 600;
  }
  .badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }
  .badge.domain { background: rgba(108, 140, 255, 0.15); color: var(--accent-light); }
  .badge.confidence { background: rgba(74, 222, 128, 0.12); color: var(--success); }
  .badge.duration { background: rgba(251, 191, 36, 0.12); color: var(--warning); }

  /* Sections */
  .report-section {
    display: none;
    padding: 32px;
    animation: fadeIn 0.3s ease;
  }
  .report-section.active {
    display: block;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .report-section h2 {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .section-icon { font-size: 24px; }
  .section-body { max-width: 960px; }

  /* Cards grid */
  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .card-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
  }
  .card-value {
    font-size: 18px;
    font-weight: 600;
  }
  .card-primary .card-value { color: var(--accent-light); }
  .card-info .card-value { color: var(--info); }
  .card-success .card-value { color: var(--success); }
  .card-warning .card-value { color: var(--warning); }
  .card-error .card-value { color: var(--error); }
  .card-neutral .card-value { color: var(--text-primary); }

  /* Flags */
  .flags-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
  }
  .flag {
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
  }
  .flag-on {
    background: rgba(74, 222, 128, 0.12);
    color: var(--success);
    border: 1px solid rgba(74, 222, 128, 0.25);
  }
  .flag-off {
    background: rgba(107, 111, 136, 0.1);
    color: var(--text-muted);
    border: 1px solid var(--border);
  }

  .jira-summary, .root-cause-brief {
    font-size: 15px;
    color: var(--text-secondary);
    margin-bottom: 20px;
    line-height: 1.6;
  }

  /* Root cause box */
  .root-cause-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin: 16px 0;
    color: var(--text-primary);
    font-size: 15px;
    line-height: 1.7;
  }
  .root-cause-box p {
    margin: 8px 0;
  }
  .root-cause-box ul,
  .root-cause-box ol {
    margin: 12px 0;
    padding-left: 24px;
  }
  .root-cause-box li {
    margin: 6px 0;
  }
  .root-cause-box code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    background: rgba(0, 200, 83, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }
  .root-cause-box pre {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 12px 16px;
    margin: 12px 0;
    overflow-x: auto;
  }

  /* Fix recommendation */
  .fix-recommendation {
    background: rgba(74, 222, 128, 0.06);
    border: 1px solid rgba(74, 222, 128, 0.2);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin: 16px 0;
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.7;
  }
  .fix-recommendation ol,
  .fix-recommendation ul {
    margin: 12px 0;
    padding-left: 24px;
  }
  .fix-recommendation li {
    margin: 8px 0;
    line-height: 1.6;
  }
  .fix-recommendation pre {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px 16px;
    margin: 12px 0;
    overflow-x: auto;
    font-size: 13px;
  }
  .fix-recommendation code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    background: rgba(0, 200, 83, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }
  .fix-recommendation pre code {
    background: transparent;
    padding: 0;
  }
  .fix-recommendation h4 {
    color: var(--text-primary);
    font-size: 14px;
    margin: 16px 0 8px 0;
  }
  .fix-recommendation p {
    margin: 8px 0;
  }

  /* Confidence bar */
  .confidence-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
  }
  .confidence-label {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    min-width: 140px;
  }
  .confidence-track {
    flex: 1;
    height: 8px;
    background: var(--bg-card);
    border-radius: 4px;
    overflow: hidden;
    max-width: 300px;
  }
  .confidence-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--warning), var(--success));
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  /* Component tags */
  .components-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0;
  }
  .component-tag {
    padding: 4px 12px;
    background: rgba(96, 165, 250, 0.1);
    color: var(--info);
    border-radius: 16px;
    font-size: 13px;
    font-weight: 500;
  }

  /* Code diff */
  .fix-item {
    margin: 24px 0;
    padding: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  .fix-item h4 {
    margin-bottom: 8px;
    color: var(--text-primary);
  }
  .fix-description {
    color: var(--text-muted);
    font-size: 14px;
    margin-bottom: 16px;
  }
  .code-diff-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .code-diff-block {
    border-radius: var(--radius);
    overflow: hidden;
  }
  .diff-header {
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .diff-remove .diff-header {
    background: rgba(248, 113, 113, 0.15);
    color: var(--error);
  }
  .diff-add .diff-header {
    background: rgba(74, 222, 128, 0.15);
    color: var(--success);
  }
  .code-diff-block .code-block {
    margin: 0;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
  }

  /* Code blocks */
  .code-block, pre.code-block {
    background: #0d0f16;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    overflow-x: auto;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: var(--text-secondary);
    margin: 12px 0;
    white-space: pre;
  }
  .inline-code {
    background: rgba(108, 140, 255, 0.1);
    color: var(--accent-light);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.9em;
  }
  .file-ref {
    color: var(--info);
    font-size: 13px;
  }

  /* Tables */
  .steps-table, .md-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    margin: 12px 0;
  }
  .steps-table th, .md-table th {
    text-align: left;
    padding: 10px 14px;
    background: var(--bg-card);
    color: var(--text-muted);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 2px solid var(--border);
  }
  .steps-table td, .md-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
  }
  .steps-table tbody tr:hover, .md-table tbody tr:hover {
    background: var(--bg-hover);
  }
  .steps-table tfoot td {
    border-top: 2px solid var(--border);
    padding-top: 12px;
    color: var(--text-primary);
  }
  .status-ok { color: var(--success); }
  .status-error { color: var(--warning); }
  .bar-cell {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .bar {
    height: 6px;
    background: var(--accent);
    border-radius: 3px;
    min-width: 2px;
    transition: width 0.3s ease;
  }
  .bar-cell span {
    font-size: 12px;
    color: var(--text-muted);
    min-width: 40px;
  }

  .empty-notice {
    color: var(--text-muted);
    font-style: italic;
    padding: 24px;
    text-align: center;
  }

  /* Markdown body */
  .markdown-body h1, .markdown-body h2, .markdown-body h3,
  .markdown-body h4, .markdown-body h5, .markdown-body h6 {
    margin: 20px 0 10px;
    font-weight: 600;
    color: var(--text-primary);
  }
  .markdown-body h1 { font-size: 24px; }
  .markdown-body h2 { font-size: 20px; }
  .markdown-body h3 { font-size: 17px; }
  .markdown-body p {
    margin: 8px 0;
    color: var(--text-secondary);
    line-height: 1.7;
  }
  .markdown-body strong { color: var(--text-primary); }
  .markdown-body ul, .markdown-body ol {
    margin: 8px 0 8px 24px;
    color: var(--text-secondary);
  }
  .markdown-body li { margin: 4px 0; }
  .markdown-body hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 20px 0;
  }
  .markdown-body a {
    color: var(--accent-light);
    text-decoration: none;
  }
  .markdown-body a:hover { text-decoration: underline; }

  /* Responsive */
  @media (max-width: 900px) {
    .sidebar { transform: translateX(-100%); }
    .sidebar.open { transform: translateX(0); }
    .content { margin-left: 0; }
    .menu-toggle { display: block; }
    .report-section { padding: 20px 16px; }
    .cards-grid { grid-template-columns: repeat(2, 1fr); }
    .code-diff-container { grid-template-columns: 1fr; }
  }

  /* Print */
  @media print {
    .sidebar, .menu-toggle { display: none !important; }
    .content { margin-left: 0; }
    .top-bar { position: static; }
    body { background: #fff; color: #111; }
    .report-section { display: block !important; page-break-inside: avoid; border-bottom: 1px solid #ddd; animation: none !important; }
    .card { border: 1px solid #ddd; background: #f9f9f9; }
    .card-value { color: #111 !important; }
  }
</style>'''


def get_scripts() -> str:
    """Return embedded JavaScript for the main report."""
    return '''<script>
  (function() {
    var navLinks = document.querySelectorAll('.nav-link');
    var allSections = document.querySelectorAll('.report-section');

    window.showSection = function(sectionId) {
      allSections.forEach(function(s) {
        s.classList.remove('active');
      });
      var target = document.getElementById(sectionId);
      if (target) {
        target.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      navLinks.forEach(function(link) {
        link.classList.toggle('active', link.dataset.section === sectionId);
      });
      document.getElementById('sidebar').classList.remove('open');
    };

    navLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        showSection(link.dataset.section);
      });
    });

    showSection('overview');
  })();

  function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
  }

  function toggleCollapsible(btn) {
    var content = btn.nextElementSibling;
    var isOpen = content.classList.toggle('open');
    btn.textContent = isOpen
      ? btn.textContent.replace('Show', 'Hide')
      : btn.textContent.replace('Hide', 'Show');
  }
</script>'''


def get_standalone_styles() -> str:
    """Return embedded CSS styles for standalone reports."""
    return '''<style>
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
    --radius: 8px;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 32px;
    height: 60px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 50;
  }
  .header-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .header-icon { font-size: 24px; }
  .header-info h1 {
    font-size: 20px;
    font-weight: 600;
  }
  .badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }
  .badge.primary { background: rgba(108, 140, 255, 0.15); color: var(--accent-light); }
  .badge.domain { background: rgba(74, 222, 128, 0.12); color: var(--success); }
  .timestamp {
    font-size: 12px;
    color: var(--text-muted);
  }

  .content {
    flex: 1;
    max-width: 960px;
    margin: 0 auto;
    padding: 32px;
    width: 100%;
  }

  .footer {
    padding: 16px 32px;
    border-top: 1px solid var(--border);
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
  }

  .markdown-body h1, .markdown-body h2, .markdown-body h3,
  .markdown-body h4, .markdown-body h5, .markdown-body h6 {
    margin: 20px 0 10px;
    font-weight: 600;
    color: var(--text-primary);
  }
  .markdown-body h1 { font-size: 24px; }
  .markdown-body h2 { font-size: 20px; }
  .markdown-body h3 { font-size: 17px; }
  .markdown-body p {
    margin: 8px 0;
    color: var(--text-secondary);
    line-height: 1.7;
  }
  .markdown-body strong { color: var(--text-primary); }
  .markdown-body ul, .markdown-body ol {
    margin: 8px 0 8px 24px;
    color: var(--text-secondary);
  }
  .markdown-body li { margin: 4px 0; }
  .markdown-body hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 20px 0;
  }
  .markdown-body a {
    color: var(--accent-light);
    text-decoration: none;
  }
  .markdown-body a:hover { text-decoration: underline; }

  .code-block, pre.code-block {
    background: #0d0f16;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    overflow-x: auto;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: var(--text-secondary);
    margin: 12px 0;
    white-space: pre;
  }
  .inline-code {
    background: rgba(108, 140, 255, 0.1);
    color: var(--accent-light);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.9em;
  }
  .file-ref {
    color: var(--info);
    font-size: 13px;
  }

  .md-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    margin: 12px 0;
  }
  .md-table th {
    text-align: left;
    padding: 10px 14px;
    background: var(--bg-card);
    color: var(--text-muted);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 2px solid var(--border);
  }
  .md-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
  }
  .md-table tbody tr:hover {
    background: var(--bg-hover);
  }

  @media (max-width: 700px) {
    .content { padding: 16px; }
    .top-bar { padding: 0 16px; }
  }

  @media print {
    .top-bar { position: static; }
    body { background: #fff; color: #111; }
    .markdown-body p { color: #333; }
    .code-block { background: #f5f5f5; color: #333; border-color: #ddd; }
  }
</style>'''


def get_standalone_scripts() -> str:
    """Return embedded JavaScript for standalone reports."""
    return '''<script>
  function toggleCollapsible(btn) {
    var content = btn.nextElementSibling;
    var isOpen = content.classList.toggle('open');
    btn.textContent = isOpen
      ? btn.textContent.replace('Show', 'Hide')
      : btn.textContent.replace('Hide', 'Show');
  }
</script>'''


# ============================================================================
# Convenience Functions
# ============================================================================

def save_html_report(
    rca_result: Dict[str, Any],
    output_path: str,
    defect_data: Dict[str, Any] = None
) -> str:
    """
    Generate and save the HTML report to a file.
    
    Args:
        rca_result: RCA analysis result
        output_path: Path to save the HTML file
        defect_data: Optional defect data
        
    Returns:
        Path to the saved file
    """
    html_content = generate_rca_html_report(rca_result, defect_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def save_standalone_report(
    jira_key: str,
    title: str,
    icon: str,
    markdown_content: str,
    output_path: str,
    badge: str = None
) -> str:
    """
    Generate and save a standalone HTML report to a file.
    
    Args:
        jira_key: JIRA key
        title: Report title
        icon: Icon emoji
        markdown_content: Markdown content
        output_path: Path to save the HTML file
        badge: Optional badge text
        
    Returns:
        Path to the saved file
    """
    html_content = generate_standalone_html_report(
        jira_key, title, icon, markdown_content, badge
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path
