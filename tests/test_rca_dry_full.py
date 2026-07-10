"""
Dry Test: Full RCA Analysis with Dashboard - No JIRA

This test:
1. Starts the real-time dashboard
2. Runs full RCA analysis on usb_str_slow.dlt
3. Tracks tokens live in dashboard
4. Generates HTML report
5. NO JIRA interaction

Usage:
    python test_rca_dry_full.py
"""

import os
import sys
import time
import json
import threading
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rca_infotainment.dlt_analyzer import DLTAnalyzer
from rca_infotainment.html_report_generator import generate_rca_html_report
from rca_infotainment.dashboard.dashboard_server import RCADashboard


def run_rca_analysis_with_tracking(dashboard: RCADashboard, defect_id: str, dlt_file: str):
    """
    Run full RCA analysis with live dashboard tracking
    
    Args:
        dashboard: Dashboard instance for live updates
        defect_id: Ticket ID
        dlt_file: Path to DLT log file
    """
    print(f"\n{'='*60}")
    print(f"  RCA Analysis: {defect_id}")
    print(f"  DLT File: {dlt_file}")
    print(f"{'='*60}\n")
    
    # Token metrics tracking
    token_metrics = {
        "by_stage": {},
        "total_input": 0,
        "total_output": 0,
        "total_tokens": 0,
        "estimated_cost_eur": 0.0
    }
    
    def track_tokens(stage: str, input_tok: int, output_tok: int):
        """Track tokens for a stage"""
        total = input_tok + output_tok
        cost = total * 0.000037
        
        if stage not in token_metrics["by_stage"]:
            token_metrics["by_stage"][stage] = {"input": 0, "output": 0, "total": 0}
        
        token_metrics["by_stage"][stage]["input"] += input_tok
        token_metrics["by_stage"][stage]["output"] += output_tok
        token_metrics["by_stage"][stage]["total"] += total
        
        token_metrics["total_input"] += input_tok
        token_metrics["total_output"] += output_tok
        token_metrics["total_tokens"] += total
        token_metrics["estimated_cost_eur"] += cost
        
        # Send to dashboard
        dashboard.add_tokens(defect_id, stage, input_tok, output_tok)
        
        print(f"    + {total:,} tokens ({stage}) → Total: {token_metrics['total_tokens']:,}")
    
    # Mock defect data
    defect_data = {
        "key": defect_id,
        "summary": "[USB] Source switch from FM to USB takes more than 200ms (STR KPI failure)",
        "description": "When user taps USB source button, the source-to-render time exceeds 200ms threshold. Observed 378ms delay.",
        "priority": "High",
        "component": "Media",
        "status": "Open",
        "reporter": "Test User",
        "created": datetime.now().isoformat(),
        "sw_version": "SW_2026.06.01_R1",
        "dlt_attachment": os.path.basename(dlt_file)
    }
    
    # Start analysis tracking
    dashboard.start_analysis(defect_id, {
        "summary": defect_data["summary"][:100],
        "component": defect_data["component"],
        "priority": defect_data["priority"]
    })
    
    start_time = time.time()
    
    # ========================================
    # Stage 1: Load Defect
    # ========================================
    print("[1/6] Loading defect data...")
    dashboard.update_stage(defect_id, "defect_loading", "running")
    time.sleep(0.3)
    dashboard.update_stage(defect_id, "defect_loading", "completed")
    print("      Defect loaded successfully")
    
    # ========================================
    # Stage 2: DLT Analysis
    # ========================================
    print("\n[2/6] Analyzing DLT logs...")
    dashboard.update_stage(defect_id, "dlt_analysis", "running")
    
    # Read and parse DLT file
    with open(dlt_file, 'r', encoding='utf-8') as f:
        dlt_content = f.read()
    
    # Simulate token consumption for DLT parsing prompt
    track_tokens("dlt_analysis", len(dlt_content) // 4, 0)
    time.sleep(0.5)
    
    # Parse DLT
    analyzer = DLTAnalyzer()
    dlt_analysis = analyzer.analyze(dlt_content)
    
    # Add structured data
    dlt_analysis["errors"] = [
        {"timestamp": "2026/06/10 10:00:00.500000", "message": "[MEDIA] STR KPI FAILED duration=378ms > threshold=200ms", "severity": "WARNING"}
    ]
    dlt_analysis["warnings"] = ["[MEDIA] STR KPI FAILED duration=378ms > threshold=200ms"]
    dlt_analysis["components"] = ["USB", "MEDIA", "AUDIO", "HMI"]
    dlt_analysis["domain"] = "Media"
    
    track_tokens("dlt_analysis", 0, 300)
    time.sleep(0.3)
    
    dashboard.update_stage(defect_id, "dlt_analysis", "completed")
    print(f"      Found {len(dlt_analysis.get('errors', []))} errors, {len(dlt_analysis.get('warnings', []))} warnings")
    print(f"      Components: {', '.join(dlt_analysis.get('components', []))}")
    
    # ========================================
    # Stage 3: Source Mapping
    # ========================================
    print("\n[3/6] Mapping to source code...")
    dashboard.update_stage(defect_id, "source_mapping", "running")
    
    track_tokens("source_mapping", 400, 0)
    time.sleep(0.4)
    
    source_mapping = {
        "mapped_files": [
            {"file": "src/media/usb/USBMediaService.cpp", "reason": "USB service implementation", "confidence": 0.95},
            {"file": "src/media/usb/USBDeviceEnumerator.cpp", "reason": "Device enumeration logic", "confidence": 0.92},
            {"file": "src/media/SourceManager.cpp", "reason": "Source switching orchestration", "confidence": 0.85},
            {"file": "src/audio/AudioFocusManager.cpp", "reason": "Audio focus handling", "confidence": 0.78}
        ]
    }
    
    track_tokens("source_mapping", 0, 150)
    time.sleep(0.3)
    
    dashboard.update_stage(defect_id, "source_mapping", "completed")
    print(f"      Mapped {len(source_mapping['mapped_files'])} source files")
    
    # ========================================
    # Stage 4: Historical Match
    # ========================================
    print("\n[4/6] Searching historical defects...")
    dashboard.update_stage(defect_id, "historical_match", "running")
    
    track_tokens("historical_match", 600, 0)
    time.sleep(0.5)
    
    historical_matches = [
        {"defect_id": "SAM1-1890", "similarity_score": 0.89, "summary": "[USB] Source switch slow on certain USB drives", "root_cause": "USB device enumeration delay"},
        {"defect_id": "SAM1-1456", "similarity_score": 0.72, "summary": "[Media] STR KPI intermittently failing", "root_cause": "Audio service initialization delay"},
        {"defect_id": "SAM1-1234", "similarity_score": 0.65, "summary": "[Audio] Focus acquisition takes too long", "root_cause": "AudioFocusManager lock contention"},
    ]
    
    track_tokens("historical_match", 0, 250)
    time.sleep(0.3)
    
    dashboard.update_stage(defect_id, "historical_match", "completed")
    print(f"      Found {len(historical_matches)} similar defects")
    for m in historical_matches:
        print(f"        - {m['defect_id']}: {m['similarity_score']:.0%} similar")
    
    # ========================================
    # Stage 5: LLM Analysis (main token consumer)
    # ========================================
    print("\n[5/6] Running LLM analysis...")
    dashboard.update_stage(defect_id, "llm_analysis", "running")
    
    # Simulate incremental LLM token consumption
    print("      Sending prompt to LLM...")
    track_tokens("llm_analysis", 1500, 0)
    time.sleep(0.5)
    
    print("      Analyzing root cause...")
    track_tokens("llm_analysis", 0, 400)
    time.sleep(0.5)
    
    print("      Generating evidence...")
    track_tokens("llm_analysis", 0, 350)
    time.sleep(0.4)
    
    print("      Creating fix recommendations...")
    track_tokens("llm_analysis", 0, 500)
    time.sleep(0.5)
    
    print("      Generating code fixes...")
    track_tokens("llm_analysis", 0, 600)
    time.sleep(0.5)
    
    # LLM Analysis result
    llm_analysis = {
        "root_cause": """The STR (Source-To-Render) KPI failure is caused by excessive USB device enumeration time.

The USB device enumeration took 177ms out of the total 378ms, which is 47% of the total delay. Combined with:
- Source manager state transitions: ~50ms  
- Audio focus acquisition: ~23ms
- MediaPlayer track preparation: ~89ms

The primary bottleneck is the USB device enumeration phase. The generic USB vendor (vendor_id=0x1234) device takes longer to enumerate compared to known vendor devices.

Contributing factors:
1. No cached device info for this vendor
2. Full filesystem type check performed (FAT32)
3. Sequential enumeration instead of parallel operations""",
        
        "evidence": [
            "USBMediaService device enumeration complete vendor=Generic delay=177ms",
            "MARKER STR source=USB duration=378 ms threshold=200ms",
            "STR KPI FAILED duration=378ms > threshold=200ms",
            "USBMediaService checking filesystem type=FAT32"
        ],
        
        "affected_files": [
            "src/media/usb/USBMediaService.cpp",
            "src/media/usb/USBDeviceEnumerator.cpp",
            "src/media/SourceManager.cpp"
        ],
        
        "fix_recommendation": "Implement USB device caching, parallelize filesystem check, add async enumeration with timeout fallback.",
        
        "confidence": 0.87,
        "domain": "Media",
        
        "code_fixes": [
            {
                "file_path": "src/media/usb/USBDeviceEnumerator.cpp",
                "description": "Add device caching and parallel enumeration",
                "old_content": """status_t USBDeviceEnumerator::enumerateDevice(int vendorId) {
    DeviceInfo info = queryDeviceInfo(vendorId);
    FileSystemType fsType = checkFilesystem(info.mountPoint);
    waitForDeviceReady(info.devicePath);
    return OK;
}""",
                "new_content": """status_t USBDeviceEnumerator::enumerateDevice(int vendorId) {
    // Check cache first
    if (mDeviceCache.contains(vendorId)) {
        ALOGI("Using cached device info for vendor 0x%04x", vendorId);
        return OK;
    }
    
    // Parallel enumeration with timeout
    auto infoFuture = std::async(std::launch::async, 
        &USBDeviceEnumerator::queryDeviceInfo, this, vendorId);
    auto fsFuture = std::async(std::launch::async,
        &USBDeviceEnumerator::checkFilesystemAsync, this);
    
    if (infoFuture.wait_for(100ms) == std::future_status::timeout) {
        ALOGW("Device info timeout, using defaults");
        return handleTimeout(vendorId);
    }
    
    mDeviceCache.put(vendorId, infoFuture.get());
    return OK;
}"""
            }
        ],
        
        "token_metrics": token_metrics
    }
    
    # Update confidence on dashboard
    dashboard.update_confidence(defect_id, llm_analysis["confidence"], llm_analysis["domain"])
    
    dashboard.update_stage(defect_id, "llm_analysis", "completed")
    print(f"      Root cause identified (confidence: {llm_analysis['confidence']:.0%})")
    
    # ========================================
    # Stage 6: Report Generation
    # ========================================
    print("\n[6/6] Generating reports...")
    dashboard.update_stage(defect_id, "report_generation", "running")
    
    track_tokens("report_generation", 200, 0)
    time.sleep(0.3)
    
    # Build RCA result for HTML generator
    rca_result = {
        "defect_id": defect_id,
        "status": "completed",
        "duration_seconds": time.time() - start_time,
        "stages": {
            "dlt_analysis": {"status": "completed", "data": dlt_analysis, "duration": 1.0},
            "source_mapping": {"status": "completed", "data": source_mapping, "duration": 0.7},
            "historical_match": {"status": "completed", "data": {"matches": historical_matches}, "duration": 0.8},
            "llm_analysis": {"status": "completed", "data": llm_analysis, "duration": 3.0}
        }
    }
    
    # Generate HTML report
    html_content = generate_rca_html_report(rca_result, defect_data)
    
    # Save report
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    html_path = os.path.join(output_dir, f"{defect_id}_rca.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    track_tokens("report_generation", 0, 100)
    
    dashboard.update_stage(defect_id, "report_generation", "completed")
    print(f"      HTML report saved: {html_path}")
    
    # Complete analysis
    duration = time.time() - start_time
    dashboard.complete_analysis(defect_id, success=True)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"  Defect ID:      {defect_id}")
    print(f"  Duration:       {duration:.1f}s")
    print(f"  Confidence:     {llm_analysis['confidence']:.0%}")
    print(f"  Domain:         {llm_analysis['domain']}")
    print(f"  Root Cause:     {llm_analysis['root_cause'][:80]}...")
    print(f"\n  Token Consumption:")
    print(f"  ┌─────────────────────┬──────────┬──────────┬──────────┐")
    print(f"  │ Stage               │ Input    │ Output   │ Total    │")
    print(f"  ├─────────────────────┼──────────┼──────────┼──────────┤")
    for stage, tokens in token_metrics["by_stage"].items():
        print(f"  │ {stage:<19} │ {tokens['input']:>8,} │ {tokens['output']:>8,} │ {tokens['total']:>8,} │")
    print(f"  ├─────────────────────┼──────────┼──────────┼──────────┤")
    print(f"  │ TOTAL               │ {token_metrics['total_input']:>8,} │ {token_metrics['total_output']:>8,} │ {token_metrics['total_tokens']:>8,} │")
    print(f"  └─────────────────────┴──────────┴──────────┴──────────┘")
    print(f"  Estimated Cost: €{token_metrics['estimated_cost_eur']:.4f}")
    print(f"\n  Reports:")
    print(f"    - HTML: {html_path}")
    print(f"{'='*60}\n")
    
    return {
        "defect_id": defect_id,
        "duration": duration,
        "confidence": llm_analysis["confidence"],
        "token_metrics": token_metrics,
        "html_report": html_path
    }


def main():
    """Main function"""
    
    print("\n" + "="*60)
    print("  RCA Monitoring Dashboard - Dry Test (No JIRA)")
    print("="*60 + "\n")
    
    # DLT file path - use relative paths for portability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dlt_file = os.path.join(script_dir, "data", "dlt_logs", "usb_str_slow.dlt")
    
    # Check if file exists
    if not os.path.exists(dlt_file):
        # Try alternate location
        dlt_file = os.path.join(script_dir, "attachments", "usb_str_slow.dlt")
        if not os.path.exists(dlt_file):
            print(f"ERROR: DLT file not found!")
            print("Tried:")
            print(f"  - {os.path.join(script_dir, 'data', 'dlt_logs', 'usb_str_slow.dlt')}")
            print(f"  - {os.path.join(script_dir, 'attachments', 'usb_str_slow.dlt')}")
            return
    
    print(f"Using DLT file: {dlt_file}")
    print(f"File size: {os.path.getsize(dlt_file):,} bytes\n")
    
    # Start dashboard
    dashboard = RCADashboard()  # Uses env vars or defaults
    dashboard.start()  # Uses env var DASHBOARD_AUTO_OPEN or defaults to True
    
    print(f"Dashboard running at http://{dashboard.host}:{dashboard.port}")
    print("Watch for live token updates!\n")
    
    # Wait for browser
    time.sleep(2)
    
    # Run analysis
    result = run_rca_analysis_with_tracking(
        dashboard=dashboard,
        defect_id="TEST-DRY-001",
        dlt_file=dlt_file
    )
    
    print("\n" + "-"*60)
    print("  Dashboard will keep running. Press Ctrl+C to stop.")
    print("-"*60 + "\n")
    
    # Open report in browser
    import webbrowser
    webbrowser.open(f'file:///{os.path.abspath(result["html_report"])}')
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        dashboard.stop()


if __name__ == "__main__":
    main()
