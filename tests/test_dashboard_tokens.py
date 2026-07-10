"""
Test: RCA Analysis with Live Dashboard - Token Tracking Demo

This test demonstrates:
1. Starting the dashboard server
2. Running RCA analysis with live token tracking
3. Tokens incrementing in real-time on dashboard
4. Final token metrics added to JIRA comment

Run this script and watch the dashboard at http://localhost:5050
"""

import os
import sys
import time
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rca_infotainment.dashboard.dashboard_server import RCADashboard


def simulate_rca_analysis(dashboard: RCADashboard, ticket_id: str):
    """Simulate a full RCA analysis with incremental token tracking"""
    
    print(f"\n{'='*60}")
    print(f"  Starting RCA Analysis: {ticket_id}")
    print(f"{'='*60}\n")
    
    # Start analysis
    dashboard.start_analysis(ticket_id, {
        "summary": "[USB] Source switch from FM to USB takes more than 200ms (STR KPI failure)",
        "component": "Media",
        "priority": "High"
    })
    
    # Define stages with simulated token consumption
    stages = [
        # (stage_name, duration_sec, [(input_tokens, output_tokens, delay_sec), ...])
        ("defect_loading", 0.5, []),
        ("dlt_analysis", 1.2, [
            (500, 0, 0.3),    # Initial prompt
            (0, 150, 0.5),   # First response chunk
            (0, 100, 0.4),   # Second response chunk
        ]),
        ("source_mapping", 0.8, [
            (300, 0, 0.2),
            (0, 80, 0.6),
        ]),
        ("historical_match", 1.0, [
            (800, 0, 0.3),
            (0, 200, 0.4),
            (0, 150, 0.3),
        ]),
        ("llm_analysis", 3.0, [
            (1500, 0, 0.2),   # Large prompt with all context
            (0, 300, 0.5),   # Root cause chunk
            (0, 400, 0.6),   # Evidence chunk
            (0, 350, 0.5),   # Fix recommendation chunk
            (0, 450, 0.7),   # Code fix chunk
            (0, 200, 0.5),   # Final analysis
        ]),
        ("report_generation", 0.6, [
            (200, 0, 0.3),
            (0, 100, 0.3),
        ]),
    ]
    
    total_input = 0
    total_output = 0
    
    for stage_name, base_duration, token_chunks in stages:
        print(f"  [{stage_name}] Starting...")
        dashboard.update_stage(ticket_id, stage_name, "running")
        
        if token_chunks:
            # Process token chunks with incremental updates
            for input_tok, output_tok, delay in token_chunks:
                time.sleep(delay)
                
                if input_tok > 0 or output_tok > 0:
                    dashboard.add_tokens(ticket_id, stage_name, input_tok, output_tok)
                    total_input += input_tok
                    total_output += output_tok
                    
                    chunk_type = "input" if input_tok > 0 else "output"
                    tokens = input_tok if input_tok > 0 else output_tok
                    print(f"    + {tokens:,} {chunk_type} tokens (total: {total_input + total_output:,})")
        else:
            time.sleep(base_duration)
        
        print(f"  [{stage_name}] Completed")
        dashboard.update_stage(ticket_id, stage_name, "completed")
    
    # Update final confidence
    print(f"\n  Updating confidence: 87%")
    dashboard.update_confidence(ticket_id, 0.87, "Media")
    
    time.sleep(0.5)
    
    # Complete analysis
    dashboard.complete_analysis(ticket_id, success=True)
    
    print(f"\n{'='*60}")
    print(f"  Analysis Complete!")
    print(f"  Total Input Tokens:  {total_input:,}")
    print(f"  Total Output Tokens: {total_output:,}")
    print(f"  Total Tokens:        {total_input + total_output:,}")
    print(f"  Estimated Cost:      €{(total_input + total_output) * 0.000037:.4f}")
    print(f"{'='*60}\n")
    
    return {
        "total_input": total_input,
        "total_output": total_output,
        "total_tokens": total_input + total_output
    }


def main():
    """Main function - runs dashboard with simulated analysis"""
    
    print("\n" + "="*60)
    print("  RCA MONITORING DASHBOARD - Token Tracking Demo")
    print("="*60 + "\n")
    
    # Start dashboard
    dashboard = RCADashboard(port=5050)
    dashboard.start(open_browser=True)
    
    print("Dashboard running at http://localhost:5050")
    print("Watch the dashboard for live token updates!\n")
    
    # Wait for browser to open
    time.sleep(2)
    
    # Run first analysis
    print("\n" + "-"*60)
    print("  Running Analysis #1")
    print("-"*60)
    
    result1 = simulate_rca_analysis(dashboard, "SAM1-2001")
    
    # Wait a bit
    time.sleep(2)
    
    # Run second analysis to show multiple tickets
    print("\n" + "-"*60)
    print("  Running Analysis #2")
    print("-"*60)
    
    result2 = simulate_rca_analysis(dashboard, "SAM1-2002")
    
    # Summary
    total_all = result1["total_tokens"] + result2["total_tokens"]
    print("\n" + "="*60)
    print("  SESSION SUMMARY")
    print("="*60)
    print(f"  Tickets Analyzed: 2")
    print(f"  Total Tokens:     {total_all:,}")
    print(f"  Estimated Cost:   €{total_all * 0.000037:.4f}")
    print("="*60 + "\n")
    
    print("Dashboard will keep running. Press Ctrl+C to stop.\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        dashboard.stop()


if __name__ == "__main__":
    main()
