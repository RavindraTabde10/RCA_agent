#!/usr/bin/env python
"""
RCA CLI - Command Line Interface for Root Cause Analysis Tool

Usage:
    python rca_cli.py list                      # List all defects
    python rca_cli.py stats                     # Show statistics
    python rca_cli.py search "query"            # Search historical defects
    python rca_cli.py analyze SAM1-2001         # Analyze a defect
    python rca_cli.py analyze SAM1-2001 --jira  # Analyze and upload to JIRA
    python rca_cli.py status                    # Check service status
"""

import os
import sys
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rca_infotainment.rca_engine import RCAEngine
from src.rca_infotainment.jira_service import JiraService
from src.rca_infotainment.llm_service import LLMService
from src.rca_infotainment.git_service import GitService
from src.utils.config import load_config


console = Console()


def get_config():
    """Load configuration"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.yaml')
    if os.path.exists(config_path):
        return load_config(config_path)
    return {}


def get_engine():
    """Initialize RCA engine with services"""
    config = get_config()
    engine = RCAEngine(config)
    
    # Initialize optional services
    try:
        llm_service = LLMService(config)
        if llm_service.is_available():
            engine.set_llm_client(llm_service)
    except Exception as e:
        console.print(f"[yellow]LLM service not available: {e}[/yellow]")
    
    try:
        jira_service = JiraService(config)
        if jira_service.is_connected():
            engine.set_jira_client(jira_service)
    except Exception as e:
        console.print(f"[yellow]JIRA service not available: {e}[/yellow]")
    
    # Initialize Git service for source code access
    try:
        git_config = config.get('integrations', {}).get('git', {})
        git_service = GitService(git_config)
        if git_service.is_connected():
            engine.set_git_client(git_service)
    except Exception as e:
        console.print(f"[yellow]Git service not available: {e}[/yellow]")
    
    return engine


@click.group()
@click.version_option(version='1.0.0', prog_name='RCA Tool')
def cli():
    """Root Cause Analysis Tool for Infotainment Systems
    
    Analyze defects, parse DLT logs, find duplicates, and generate reports.
    """
    pass


@cli.command()
@click.option('--limit', '-l', default=20, help='Maximum number of defects to show')
def list(limit):
    """List all current defects"""
    engine = get_engine()
    defects = engine.list_defects()
    
    if not defects:
        console.print("[yellow]No defects found[/yellow]")
        return
    
    table = Table(title=f"Current Defects ({len(defects)} total)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Summary", style="white")
    table.add_column("Component", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Status")
    
    for defect in defects[:limit]:
        table.add_row(
            defect.get('key', 'N/A'),
            defect.get('summary', 'N/A')[:50] + ('...' if len(defect.get('summary', '')) > 50 else ''),
            defect.get('component', 'N/A'),
            defect.get('priority', 'N/A'),
            defect.get('status', 'N/A')
        )
    
    console.print(table)


@cli.command()
def stats():
    """Show defect statistics"""
    engine = get_engine()
    stats = engine.get_stats()
    
    # Summary panel
    summary = f"""
[bold cyan]Current Defects:[/bold cyan] {stats['current_defects']}
[bold cyan]Historical Defects:[/bold cyan] {stats['historical_defects']}
"""
    console.print(Panel(summary, title="📊 Defect Statistics"))
    
    # By Component
    if stats.get('by_component'):
        table = Table(title="By Component")
        table.add_column("Component", style="green")
        table.add_column("Count", style="cyan")
        
        for comp, count in sorted(stats['by_component'].items(), key=lambda x: x[1], reverse=True):
            table.add_row(comp, str(count))
        
        console.print(table)
    
    # By Priority
    if stats.get('by_priority'):
        table = Table(title="By Priority")
        table.add_column("Priority", style="yellow")
        table.add_column("Count", style="cyan")
        
        for priority, count in stats['by_priority'].items():
            table.add_row(priority, str(count))
        
        console.print(table)


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=10, help='Maximum results to show')
def search(query, limit):
    """Search historical defects by keyword"""
    engine = get_engine()
    
    results = engine.historical_matcher.search_by_text(query, max_results=limit)
    
    if not results:
        console.print(f"[yellow]No matches found for '{query}'[/yellow]")
        return
    
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Summary", style="white")
    table.add_column("Component", style="green")
    table.add_column("Root Cause", style="yellow")
    
    for result in results:
        root_cause = result.get('root_cause', 'N/A')[:40]
        if len(result.get('root_cause', '')) > 40:
            root_cause += '...'
        
        table.add_row(
            result.get('defect_id', 'N/A'),
            result.get('summary', 'N/A')[:40] + '...',
            result.get('component', 'N/A'),
            root_cause
        )
    
    console.print(table)


@cli.command()
@click.argument('defect_id')
@click.option('--jira', is_flag=True, help='Upload results to JIRA')
@click.option('--no-duplicates', is_flag=True, help='Skip duplicate marking')
@click.option('--output', '-o', default=None, help='Custom output directory')
def analyze(defect_id, jira, no_duplicates, output):
    """Analyze a defect and generate RCA report
    
    Examples:
        rca_cli.py analyze SAM1-2001
        rca_cli.py analyze SAM1-2001 --jira
        rca_cli.py analyze SAM1-2001 -o ./reports
    """
    engine = get_engine()
    
    # Override output directory if specified
    if output:
        engine.output_dir = output
        os.makedirs(output, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Analyzing defect...", total=None)
        
        # Run analysis
        progress.update(task, description="Loading defect data...")
        result = engine.analyze_defect(
            defect_id=defect_id,
            from_jira=jira,
            upload_to_jira=jira,
            mark_duplicates=not no_duplicates
        )
        
        progress.update(task, description="Analysis complete!")
    
    # Display results
    if result['status'] == 'completed':
        _display_analysis_result(result)
    else:
        console.print(f"[red]Analysis failed: {result.get('error', 'Unknown error')}[/red]")


def _display_analysis_result(result):
    """Display analysis results in a nice format"""
    defect_id = result.get('defect_id', 'Unknown')
    
    # Header
    console.print()
    console.print(Panel(
        f"[bold green]Analysis Complete for {defect_id}[/bold green]",
        title="✅ RCA Results"
    ))
    
    # Duplicate warning
    duplicate_info = result.get('duplicate_info', {})
    if duplicate_info.get('is_duplicate'):
        console.print(Panel(
            f"[yellow]⚠️ This defect is {duplicate_info['similarity_score']:.0%} similar to "
            f"[bold]{duplicate_info['duplicate_of']}[/bold][/yellow]\n"
            "Consider linking as duplicate.",
            title="Potential Duplicate",
            border_style="yellow"
        ))
    
    # Root Cause
    llm_result = result.get('stages', {}).get('llm_analysis', {}).get('data', {})
    console.print(Panel(
        f"[white]{llm_result.get('root_cause', 'Unable to determine')}[/white]",
        title="🔍 Root Cause",
        border_style="cyan"
    ))
    
    # Confidence
    confidence = llm_result.get('confidence', 0)
    conf_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.5 else "red"
    console.print(f"[{conf_color}]Confidence: {confidence:.0%}[/{conf_color}]")
    console.print()
    
    # Reports generated
    reports = result.get('reports', {})
    if reports:
        table = Table(title="📄 Generated Reports")
        table.add_column("Format", style="cyan")
        table.add_column("Path", style="white")
        
        for fmt, info in reports.items():
            table.add_row(fmt.upper(), info.get('path', 'N/A'))
        
        console.print(table)
    
    # JIRA update status
    jira_result = result.get('stages', {}).get('jira_update', {}).get('data', {})
    if jira_result:
        console.print()
        status_items = []
        if jira_result.get('comment_added'):
            status_items.append("[green]✓ Comment added to JIRA[/green]")
        if jira_result.get('attachments_uploaded'):
            status_items.append("[green]✓ Reports uploaded to JIRA[/green]")
        if jira_result.get('duplicate_marked'):
            status_items.append(f"[green]✓ Linked as duplicate of {jira_result.get('duplicate_of')}[/green]")
        
        if status_items:
            console.print(Panel("\n".join(status_items), title="JIRA Updates"))


@cli.command()
def status():
    """Check service status (LLM, JIRA, Git)"""
    config = get_config()
    
    console.print(Panel("[bold]Service Status[/bold]", title="🔧 RCA Tool"))
    
    # LLM Status
    try:
        llm = LLMService(config)
        llm_status = llm.get_status()
        
        if llm.is_available():
            console.print(f"[green]✓ LLM Service:[/green] {llm_status['provider']} ({llm_status['model']})")
        else:
            console.print(f"[yellow]○ LLM Service:[/yellow] Not configured (placeholder mode)")
    except Exception as e:
        console.print(f"[red]✗ LLM Service:[/red] Error - {e}")
    
    # JIRA Status
    try:
        jira = JiraService(config)
        
        if jira.is_connected():
            console.print(f"[green]✓ JIRA Service:[/green] Connected to {jira.jira_url}")
        else:
            console.print(f"[yellow]○ JIRA Service:[/yellow] Not configured")
    except Exception as e:
        console.print(f"[red]✗ JIRA Service:[/red] Error - {e}")
    
    # Git Status
    try:
        git_config = config.get('integrations', {}).get('git', {})
        git = GitService(git_config)
        git_status = git.get_status()
        
        if git.is_connected():
            console.print(f"[green]✓ Git Service:[/green] {git_status['repo_url'] or git_status['local_path']}")
        else:
            console.print(f"[yellow]○ Git Service:[/yellow] Not configured (source code from local files)")
    except Exception as e:
        console.print(f"[red]✗ Git Service:[/red] Error - {e}")
    
    # Data paths
    console.print()
    console.print("[bold]Data Paths:[/bold]")
    
    paths = config.get('paths', {})
    defects_path = paths.get('defects_dir', 'data/defects')
    historical_path = paths.get('historical_defects', 'data/defects/historical_defects.json')
    
    if os.path.exists(defects_path):
        console.print(f"[green]✓ Defects directory:[/green] {defects_path}")
    else:
        console.print(f"[yellow]○ Defects directory:[/yellow] {defects_path} (not found)")
    
    if os.path.exists(historical_path):
        console.print(f"[green]✓ Historical defects:[/green] {historical_path}")
    else:
        console.print(f"[yellow]○ Historical defects:[/yellow] {historical_path} (not found)")


@cli.command()
@click.argument('defect_id')
def check_duplicate(defect_id):
    """Check if a defect is a potential duplicate"""
    engine = get_engine()
    
    defects = engine.list_defects()
    defect_data = None
    
    for d in defects:
        if d.get('key') == defect_id:
            defect_data = d
            break
    
    if not defect_data:
        console.print(f"[red]Defect {defect_id} not found[/red]")
        return
    
    duplicate = engine.historical_matcher.check_duplicate(defect_data)
    
    if duplicate:
        console.print(Panel(
            f"[yellow]This defect is [bold]{duplicate['similarity_score']:.0%}[/bold] similar to "
            f"[bold cyan]{duplicate['duplicate_of']}[/bold cyan][/yellow]\n\n"
            f"Original Root Cause: {duplicate.get('original_root_cause', 'N/A')[:100]}...",
            title="⚠️ Duplicate Detected",
            border_style="yellow"
        ))
    else:
        console.print("[green]No duplicate detected[/green]")


@cli.command()
@click.argument('defect_id')
def view_report(defect_id):
    """View the generated report for a defect"""
    config = get_config()
    output_dir = config.get('paths', {}).get('output_dir', 'output/reports')
    
    md_path = os.path.join(output_dir, f"{defect_id}_rca.md")
    html_path = os.path.join(output_dir, f"{defect_id}_rca.html")
    
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        console.print(Panel(content[:2000] + "...", title=f"Report: {defect_id}"))
        console.print(f"\n[cyan]Full report: {md_path}[/cyan]")
        console.print(f"[cyan]HTML report: {html_path}[/cyan]")
    else:
        console.print(f"[yellow]No report found for {defect_id}[/yellow]")
        console.print(f"[dim]Run 'analyze {defect_id}' to generate a report[/dim]")


if __name__ == '__main__':
    cli()
