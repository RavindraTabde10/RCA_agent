"""
Dry Test: Generate RCA HTML Report without JIRA interaction

This test script:
1. Loads the USB STR slow DLT log
2. Runs DLT analysis
3. Generates mock RCA analysis
4. Produces the HTML report
5. Opens it in browser for preview

No JIRA interaction - purely local test.
"""

import os
import sys
import json
import webbrowser
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rca_infotainment.dlt_analyzer import DLTAnalyzer
from rca_infotainment.html_report_generator import generate_rca_html_report, save_html_report


def run_dry_test():
    """Run dry test to generate HTML report from DLT log"""
    
    print("=" * 60)
    print("RCA HTML Report Generator - Dry Test")
    print("=" * 60)
    print()
    
    # Paths
    dlt_file = r"E:\RCA_agent\RCA_agent\attachments\usb_str_slow.dlt"
    output_dir = r"E:\RCA_agent\RCA_agent\output"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Mock defect data
    defect_id = "TEST-001"
    defect_data = {
        "key": defect_id,
        "summary": "[USB] Source switch from FM to USB takes more than 200ms (STR KPI failure)",
        "description": "When user taps USB source button, the source-to-render time exceeds 200ms threshold. Observed 378ms delay.",
        "priority": "High",
        "component": "Media",
        "status": "Open",
        "reporter": "Test User",
        "created": "2026-06-10T10:00:00.000Z",
        "sw_version": "SW_2026.06.01_R1",
        "dlt_attachment": "usb_str_slow.dlt"
    }
    
    print(f"[1/5] Loading DLT log: {dlt_file}")
    
    # Check if file exists
    if not os.path.exists(dlt_file):
        print(f"ERROR: DLT file not found: {dlt_file}")
        return
    
    # Read DLT file
    with open(dlt_file, 'r', encoding='utf-8') as f:
        dlt_content = f.read()
    
    print(f"      Loaded {len(dlt_content)} bytes")
    print()
    
    print("[2/5] Running DLT analysis...")
    
    # Initialize DLT analyzer and parse
    analyzer = DLTAnalyzer()
    dlt_analysis = analyzer.analyze(dlt_content)
    
    # Add extra parsed details manually since the log is simple
    dlt_analysis["errors"] = [
        {
            "timestamp": "2026/06/10 10:00:00.500000",
            "message": "[MEDIA] STR KPI FAILED duration=378ms > threshold=200ms",
            "severity": "WARNING"
        }
    ]
    dlt_analysis["warnings"] = [
        "[MEDIA] STR KPI FAILED duration=378ms > threshold=200ms"
    ]
    dlt_analysis["components"] = ["USB", "MEDIA", "AUDIO", "HMI"]
    dlt_analysis["domain"] = "Media"
    dlt_analysis["sw_version"] = "SW_2026.06.01_R1"
    dlt_analysis["timeline"] = [
        {"time": "10:00:00.000", "event": "User tap USB button"},
        {"time": "10:00:00.050", "event": "Source change requested FM → USB"},
        {"time": "10:00:00.145", "event": "USB device enumeration started"},
        {"time": "10:00:00.322", "event": "Device enumeration complete (177ms)"},
        {"time": "10:00:00.367", "event": "Audio focus requested"},
        {"time": "10:00:00.456", "event": "MediaPlayer preparing track"},
        {"time": "10:00:00.489", "event": "STR KPI FAILED: 378ms > 200ms threshold"}
    ]
    
    print(f"      Found {len(dlt_analysis.get('errors', []))} errors")
    print(f"      Found {len(dlt_analysis.get('warnings', []))} warnings")
    print(f"      Components: {', '.join(dlt_analysis.get('components', []))}")
    print()
    
    print("[3/5] Building mock LLM analysis...")
    
    # Mock LLM analysis result
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
            "USBMediaService checking filesystem type=FAT32",
            "Device vendor_id=0x1234 (unknown/generic)"
        ],
        
        "affected_files": [
            "src/media/usb/USBMediaService.cpp",
            "src/media/usb/USBDeviceEnumerator.cpp",
            "src/media/SourceManager.cpp",
            "src/audio/AudioFocusManager.cpp"
        ],
        
        "fix_recommendation": """1. Implement USB device caching to skip full enumeration for known devices
2. Parallelize filesystem check with device info query
3. Add async enumeration with timeout fallback
4. Pre-warm USB service on system boot
5. Use cached metadata for previously connected devices""",
        
        "confidence": 0.87,
        "domain": "Media",
        
        "code_fixes": [
            {
                "file_path": "src/media/usb/USBDeviceEnumerator.cpp",
                "description": "Add device caching and parallel enumeration",
                "old_content": """status_t USBDeviceEnumerator::enumerateDevice(int vendorId) {
    // Query device info synchronously
    DeviceInfo info = queryDeviceInfo(vendorId);
    
    // Check filesystem type
    FileSystemType fsType = checkFilesystem(info.mountPoint);
    
    // Wait for device ready
    waitForDeviceReady(info.devicePath);
    
    return OK;
}""",
                "new_content": """status_t USBDeviceEnumerator::enumerateDevice(int vendorId) {
    // Check cache first
    if (mDeviceCache.contains(vendorId)) {
        ALOGI("Using cached device info for vendor 0x%04x", vendorId);
        return OK;
    }
    
    // Parallel enumeration
    std::future<DeviceInfo> infoFuture = std::async(
        std::launch::async, &USBDeviceEnumerator::queryDeviceInfo, this, vendorId);
    std::future<FileSystemType> fsFuture = std::async(
        std::launch::async, &USBDeviceEnumerator::checkFilesystemAsync, this);
    
    // Wait with timeout
    if (infoFuture.wait_for(std::chrono::milliseconds(100)) == std::future_status::timeout) {
        ALOGW("Device info query timeout, using defaults");
        return handleTimeout(vendorId);
    }
    
    DeviceInfo info = infoFuture.get();
    FileSystemType fsType = fsFuture.get();
    
    // Cache for future use
    mDeviceCache.put(vendorId, info);
    
    return OK;
}"""
            },
            {
                "file_path": "src/media/SourceManager.cpp",
                "description": "Add pre-warming for USB service",
                "old_content": """void SourceManager::handleSourceChange(Source target) {
    // Stop current source
    stopCurrentSource();
    
    // Start target source
    startSource(target);
}""",
                "new_content": """void SourceManager::handleSourceChange(Source target) {
    // Pre-warm target while stopping current (parallel)
    std::thread warmupThread([this, target]() {
        preWarmSource(target);
    });
    
    // Stop current source
    stopCurrentSource();
    
    warmupThread.join();
    
    // Start target source (already pre-warmed)
    startSource(target);
}"""
            }
        ]
    }
    
    print(f"      Root cause: {llm_analysis['root_cause'][:80]}...")
    print(f"      Confidence: {llm_analysis['confidence']:.0%}")
    print(f"      Affected files: {len(llm_analysis['affected_files'])}")
    print(f"      Code fixes: {len(llm_analysis['code_fixes'])}")
    print()
    
    print("[4/5] Building historical matches...")
    
    # Mock historical matches
    historical_matches = [
        {
            "defect_id": "SAM1-1890",
            "similarity_score": 0.89,
            "summary": "[USB] Source switch slow on certain USB drives",
            "root_cause": "USB device enumeration delay due to vendor-specific quirks"
        },
        {
            "defect_id": "SAM1-1456",
            "similarity_score": 0.72,
            "summary": "[Media] STR KPI intermittently failing on cold boot",
            "root_cause": "Audio service initialization delay on cold boot"
        },
        {
            "defect_id": "SAM1-1234",
            "similarity_score": 0.65,
            "summary": "[Audio] Focus acquisition takes too long",
            "root_cause": "AudioFocusManager lock contention with TunerService"
        }
    ]
    
    print(f"      Found {len(historical_matches)} similar defects")
    for m in historical_matches:
        print(f"        - {m['defect_id']}: {m['similarity_score']:.0%} similar")
    print()
    
    print("[5/5] Generating HTML report...")
    
    # Build source mapping
    source_mapping = {
        "mapped_files": [
            {"file": "src/media/usb/USBMediaService.cpp", "reason": "USB service implementation", "confidence": 0.95},
            {"file": "src/media/usb/USBDeviceEnumerator.cpp", "reason": "Device enumeration logic", "confidence": 0.92},
            {"file": "src/media/SourceManager.cpp", "reason": "Source switching orchestration", "confidence": 0.85},
            {"file": "src/audio/AudioFocusManager.cpp", "reason": "Audio focus handling", "confidence": 0.78}
        ]
    }
    
    # Build complete RCA result
    rca_result = {
        "defect_id": defect_id,
        "status": "completed",
        "duration_seconds": 2.5,  # Mock duration
        "stages": {
            "dlt_analysis": {
                "status": "completed",
                "data": dlt_analysis,
                "duration": 0.3
            },
            "source_mapping": {
                "status": "completed",
                "data": source_mapping,
                "duration": 0.5
            },
            "historical_match": {
                "status": "completed",
                "data": {"matches": historical_matches},
                "duration": 0.8
            },
            "llm_analysis": {
                "status": "completed",
                "data": llm_analysis,
                "duration": 0.9
            }
        }
    }
    
    # Generate HTML report
    html_content = generate_rca_html_report(rca_result, defect_data)
    
    # Save to file
    output_file = os.path.join(output_dir, f"{defect_id}_rca.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    file_size = os.path.getsize(output_file)
    print(f"      Generated: {output_file}")
    print(f"      File size: {file_size:,} bytes")
    print()
    
    print("=" * 60)
    print("DRY TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print(f"HTML Report: {output_file}")
    print()
    
    # Ask to open in browser
    try:
        response = input("Open report in browser? [Y/n]: ").strip().lower()
        if response != 'n':
            webbrowser.open(f'file:///{output_file}')
            print("Report opened in browser!")
    except:
        print(f"\nTo view the report, open: {output_file}")
    
    return output_file


if __name__ == "__main__":
    run_dry_test()
