#!/usr/bin/env python3
"""
Fix domain names and add more Stability/memory defects
"""

import pandas as pd
from pathlib import Path

# Domain name mapping
DOMAIN_MAPPING = {
    "Audio System": "audio_system_domain",
    "Stability/memory": "stability_memory_domain",
    "Bluetooth connectivity": "bluetooth_connectivity_domain",
    "Boot and System": "boot_and_system_domain"
}

def update_domains_in_file(filepath):
    """Update domain names in a CSV file"""
    print(f"\n📝 Processing {filepath.name}...")
    
    df = pd.read_csv(filepath)
    
    # Show current domain distribution
    print(f"   Current domains: {df['domain'].value_counts().to_dict()}")
    
    # Replace domain names
    df['domain'] = df['domain'].replace(DOMAIN_MAPPING)
    
    # Show updated domain distribution
    print(f"   Updated domains: {df['domain'].value_counts().to_dict()}")
    
    # Save back to file
    df.to_csv(filepath, index=False)
    print(f"   ✓ Saved {len(df)} records")
    
    return df

# Additional Stability/Memory defects to add
NEW_STABILITY_DEFECTS = [
    {
        "ticket_id": "SAM1-3111",
        "summary": "Memory leak in sensor data processing",
        "description": "Sensor data buffers accumulating in memory. Memory usage increases 50MB per hour during active sensor polling.",
        "root_cause": "Sensor data processor not freeing buffers after processing complete. Missing deallocation call.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3112",
        "summary": "Application deadlock when accessing shared resource",
        "description": "Two applications simultaneously accessing shared configuration database causes deadlock. System becomes unresponsive.",
        "root_cause": "Incorrect mutex locking order between database and cache layers causing circular wait condition.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3113",
        "summary": "System crash during high memory pressure",
        "description": "Under memory pressure conditions system crashes instead of gracefully killing low priority apps.",
        "root_cause": "OOM killer policy not configured properly. Critical services being terminated before apps.",
        "domain": "stability_memory_domain",
        "priority": "P0",
        "severity": "Critical"
    },
    {
        "ticket_id": "SAM1-3114",
        "summary": "Memory fragmentation after extended operation",
        "description": "After 48+ hours memory allocation failures occur despite showing available memory. Heap severely fragmented.",
        "root_cause": "Mixed allocation patterns without compaction causing external fragmentation.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3115",
        "summary": "Thread leak in event processing system",
        "description": "Event processing threads created but never destroyed. Thread count grows over time eventually hitting limit.",
        "root_cause": "Thread pool not reaping completed worker threads. Missing thread join logic.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3116",
        "summary": "Memory corruption in IPC message passing",
        "description": "Random crashes with memory corruption detected. Occurs during heavy inter-process communication.",
        "root_cause": "Buffer overflow in IPC message serialization. Message size check missing.",
        "domain": "stability_memory_domain",
        "priority": "P0",
        "severity": "Critical"
    },
    {
        "ticket_id": "SAM1-3117",
        "summary": "Resource leak in audio stream management",
        "description": "Audio stream handles not released after playback stops. Eventually hits system resource limit.",
        "root_cause": "Audio stream cleanup callback not being invoked on stop. Resource handle leak.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3118",
        "summary": "System slowdown due to excessive logging",
        "description": "System performance degrades significantly when debug logging enabled. Disk I/O becomes bottleneck.",
        "root_cause": "Synchronous disk writes for every log message. No buffering or async I/O.",
        "domain": "stability_memory_domain",
        "priority": "P2",
        "severity": "Medium"
    },
    {
        "ticket_id": "SAM1-3119",
        "summary": "Memory leak in graphics texture cache",
        "description": "GPU texture memory continuously grows. After 6-8 hours GPU memory exhausted causing rendering failures.",
        "root_cause": "Texture cache eviction policy not working. Old textures never freed from GPU memory.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3120",
        "summary": "Stack overflow in recursive UI rendering",
        "description": "Deep UI component nesting causes stack overflow during rendering. Crash when component tree > 50 deep.",
        "root_cause": "Recursive rendering algorithm without depth limit check. Stack size insufficient.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3121",
        "summary": "Memory not released after app termination",
        "description": "Application memory not reclaimed after force quit. Memory usage remains high until reboot.",
        "root_cause": "Application keeps shared memory segments attached. Segments not destroyed on exit.",
        "domain": "stability_memory_domain",
        "priority": "P2",
        "severity": "Medium"
    },
    {
        "ticket_id": "SAM1-3122",
        "summary": "Kernel memory leak in network stack",
        "description": "Kernel memory consumption increases during network activity. Kernel OOM after extended use.",
        "root_cause": "Socket buffers not freed after connection close. Network buffer pool leak.",
        "domain": "stability_memory_domain",
        "priority": "P0",
        "severity": "Critical"
    },
    {
        "ticket_id": "SAM1-3123",
        "summary": "Race condition causing data corruption",
        "description": "User preferences occasionally corrupted. Happens when multiple processes update simultaneously.",
        "root_cause": "Missing synchronization on shared preference file writes. Race condition.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3124",
        "summary": "Memory allocation failure in low memory scenario",
        "description": "Critical allocations fail when memory low causing system instability instead of graceful degradation.",
        "root_cause": "No memory reservation for critical operations. All memory available to apps.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3125",
        "summary": "Buffer overflow in log message formatting",
        "description": "System crashes when log messages exceed buffer size. Heap corruption detected.",
        "root_cause": "Fixed size buffer for log formatting without bounds checking. sprintf overflow.",
        "domain": "stability_memory_domain",
        "priority": "P0",
        "severity": "Critical"
    },
    {
        "ticket_id": "SAM1-3126",
        "summary": "Memory leak in animation framework",
        "description": "UI animations accumulating in memory. Memory grows during heavy UI interaction.",
        "root_cause": "Animation objects created but never destroyed. Animation cleanup not called.",
        "domain": "stability_memory_domain",
        "priority": "P2",
        "severity": "Medium"
    },
    {
        "ticket_id": "SAM1-3127",
        "summary": "System hang due to priority inversion",
        "description": "Low priority thread holding lock blocks high priority thread. System becomes unresponsive.",
        "root_cause": "Priority inheritance not implemented for mutexes. Classic priority inversion.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3128",
        "summary": "Excessive memory consumption in cache layer",
        "description": "Cache grows unbounded consuming all available memory. No size limit configured.",
        "root_cause": "Cache size limit not set. LRU eviction not implemented.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    },
    {
        "ticket_id": "SAM1-3129",
        "summary": "Memory leak in event listener registration",
        "description": "Event listeners registered but never unregistered. Listener list grows causing memory leak.",
        "root_cause": "Missing unregister calls when components destroyed. Listeners accumulate.",
        "domain": "stability_memory_domain",
        "priority": "P2",
        "severity": "Medium"
    },
    {
        "ticket_id": "SAM1-3130",
        "summary": "Crash when memory allocation fails",
        "description": "Application crashes with segfault when malloc returns NULL. No null pointer check.",
        "root_cause": "Missing null check after memory allocation. Dereferencing NULL pointer.",
        "domain": "stability_memory_domain",
        "priority": "P1",
        "severity": "High"
    }
]

def main():
    print("="*80)
    print("FIXING DOMAIN NAMES AND ADDING STABILITY/MEMORY DEFECTS")
    print("="*80)
    
    # Update domain names in all three files
    df1 = update_domains_in_file(Path("domain_assignment_synthesized_data.csv"))
    df2 = update_domains_in_file(Path("domain_training_extended.csv"))
    df3 = update_domains_in_file(Path("domain_labeled_defects_detailed.csv"))
    
    # Add new Stability/memory defects to first file
    print(f"\n➕ Adding {len(NEW_STABILITY_DEFECTS)} new stability_memory_domain defects...")
    new_df = pd.DataFrame(NEW_STABILITY_DEFECTS)
    df1_updated = pd.concat([df1, new_df], ignore_index=True)
    df1_updated.to_csv("domain_assignment_synthesized_data.csv", index=False)
    print(f"   ✓ Total records in file 1: {len(df1_updated)}")
    
    # Show final statistics
    print("\n" + "="*80)
    print("FINAL DOMAIN DISTRIBUTION")
    print("="*80)
    
    all_data = pd.concat([
        df1_updated[['ticket_id', 'domain']],
        df2[['ticket_id', 'domain']],
        df3[['ticket_id', 'domain']]
    ])
    
    print(f"\nTotal records: {len(all_data)}")
    print("\nDomain distribution:")
    print(all_data['domain'].value_counts().sort_index())
    
    print("\n✅ Complete! All domain names updated and new defects added.")

if __name__ == "__main__":
    main()
