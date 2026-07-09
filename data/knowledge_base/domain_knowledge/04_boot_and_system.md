# Boot & System Services - Domain Knowledge

## Overview
The infotainment system follows a staged boot process to meet automotive KPIs for startup time while ensuring all services initialize correctly.

---

## Boot Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                      POWER ON                                │
│                    (Ignition ON)                             │
└─────────────────────────┬───────────────────────────────────┘
                          │ T=0ms
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 1: KERNEL BOOT                            │
│         - Hardware init, driver loading                      │
│         - Target: < 500ms                                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ ~456ms
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 2: SERVICES STARTUP                       │
│         - ServiceManager initialization                      │
│         - Core services: Audio, Media, Connectivity          │
│         - Target: < 2000ms cumulative                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ ~2000-2500ms
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 3: HMI / HOMESCREEN                       │
│         - UI framework initialization                        │
│         - Home screen rendering                              │
│         - Target: Total boot < 3000ms                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ ~2800-3000ms
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 4: LUM RESTORE                            │
│         - Last User Mode restoration                         │
│         - Audio source restoration                           │
│         - Target: < 500ms after homescreen                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Boot KPI Thresholds

| Phase | KPI Name | Threshold | Measurement |
|-------|----------|-----------|-------------|
| Overall | BOOT_TIME | 3000ms | Ignition to homescreen |
| Kernel | KERNEL_BOOT | 500ms | Power to kernel ready |
| Services | SERVICES_BOOT | 2000ms | Kernel to services ready |
| HMI | HMI_READY | 500ms | Services to homescreen |
| LUM | ENTLUM | 500ms | Homescreen to audio playing |

---

## ServiceManager

### Purpose
Manages lifecycle of all system services - starting, stopping, monitoring health.

### Service Startup Order
1. **Critical Services** (parallel)
   - AudioService
   - ConnectivityService
   - SystemMonitor

2. **Core Services** (parallel, after critical)
   - MediaService
   - TunerService
   - NavigationService
   - PhoneService

3. **UI Services** (after core)
   - HMIService
   - WidgetService

### Service States
```
STOPPED → STARTING → RUNNING → STOPPING → STOPPED
              ↓          ↓
           FAILED    RESTARTING
```

### Common Issues

1. **Debug Logging Overhead**
   - Symptom: Boot time regression
   - Root Cause: Debug/trace logging enabled in production build
   - DLT Pattern: `[DEBUG]` logs during boot sequence
   - Impact: 1-2 seconds added to boot time

2. **Service Init Timeout**
   - Symptom: Specific service takes too long
   - Root Cause: Resource contention, slow I/O
   - DLT Pattern: Long gap between service start logs

---

## Memory Management

### Memory Zones
| Zone | Size | Purpose |
|------|------|---------|
| System | 512MB | OS, kernel, drivers |
| Services | 1024MB | Application services |
| HMI | 256MB | UI rendering |
| Reserve | 256MB | Emergency/buffer |
| **Total** | **2048MB** | |

### Memory Thresholds
| Level | Used | Action |
|-------|------|--------|
| Normal | < 75% | Normal operation |
| Warning | 75-90% | Log warning, optional cleanup |
| Critical | 90-95% | Force garbage collection |
| Emergency | > 95% | Kill non-critical services |

### MemoryMonitor
- Polls every hour during normal operation
- Increases to every 15 minutes at Warning level
- Logs memory delta for leak detection

**Leak Detection Pattern:**
```
[MEM] MemoryMonitor hourly memory_used=1267MB delta=+22MB
[MEM] MemoryMonitor hourly memory_used=1289MB delta=+22MB
[MEM] MemoryMonitor hourly memory_used=1311MB delta=+22MB
```
- Consistent positive delta indicates leak
- 22MB/hour × 8 hours = 176MB leaked

### OOM Handling
```
Memory threshold exceeded
         │
         ▼
  Identify largest process
         │
         ▼
  Is it critical? ──Yes──► Log and continue
         │
        No
         │
         ▼
  Trigger process restart
         │
         ▼
  ServiceManager handles restart
```

---

## DLT Identifiers

### System (SYST)
| CTX_ID | Description | Key Logs |
|--------|-------------|----------|
| BOOT | Boot phases | `phase=KERNEL`, `phase=SERVICES`, `phase=HOMESCREEN` |
| MEM0 | Memory monitor | `MemoryMonitor`, `threshold exceeded`, `OOM` |
| SRVC | Service manager | `ServiceManager`, `restarting` |
| PERF | Performance | `CPU load`, `thread count` |

### Boot Logs
```
[BOOT] System power on
[BOOT] phase=KERNEL complete time=456ms
[BOOT] phase=SERVICES starting
[BOOT] phase=SERVICES complete time=2423ms
[BOOT] phase=HOMESCREEN displayed total_boot_time=2890ms
```

### Memory Logs
```
[MEM] MemoryMonitor baseline memory_used=1245MB memory_available=803MB
[MEM] MemoryMonitor hourly memory_used=1267MB delta=+22MB
[MEM] MemoryMonitor approaching threshold memory_used=1378MB threshold=1536MB
[MEM] MemoryMonitor critical memory_used=1523MB remaining=65MB
[MEM] MemoryMonitor threshold exceeded memory_used=1567MB threshold=1536MB
[MEM] OOM detected process=MediaPlayer triggering service restart
```

### Service Logs
```
[SERVICE] ServiceManager starting AudioService
[SERVICE] ServiceManager AudioService state=RUNNING
[SERVICE] ServiceManager restarting MediaService reason=OOM
```

---

## Last User Mode (LUM)

### Purpose
Restore the user's last audio state when vehicle restarts.

### Persisted State
- Audio source (USB, BT, FM, etc.)
- Volume level
- Track position (for USB/media)
- Radio preset/frequency
- EQ settings

### Restore Flow
```
Boot Complete (Homescreen displayed)
              │
              ▼
    LUM transition=ToAvailable
              │
              ▼
    Read persisted state file
    (/data/lum/radio_state.json)
              │
              ▼
    Restore source connection
              │
         ┌────┴────┐
         ▼         ▼
      Success    Failure
         │         │
         ▼         ▼
      Play     Fallback/
      audio    Default
```

### Common Issues

1. **Preset Not Persisted**
   - Symptom: Radio preset resets to 1
   - Root Cause: preset_id not saved in persistence file
   - DLT Pattern: `preset_id not found in persisted state`

2. **State Machine Stuck**
   - Symptom: BT audio doesn't restore
   - Root Cause: No transition for `profile_unavailable` event
   - DLT Pattern: `state machine stuck in CONNECTING no transition for profile_unavailable`

### DLT Identifiers
- APP_ID: `MDIA`
- CTX_ID: `LUM0`
- Key logs:
  - `LastUserMode transition=ToAvailable`
  - `LastUserMode restoreState begin source=<SRC>`
  - `MARKER ENTLUM started playing in <MS> ms`
  - `MARKER ENTLUM FAILED duration=<MS>ms reason=<REASON>`

---

## RCA Decision Tree: Boot Issues

```
Boot Time Exceeded
       │
       ▼
┌───────────────────┐
│ Which phase slow? │
└────────┬──────────┘
    ┌────┼────┬────────┐
    ▼    ▼    ▼        ▼
KERNEL SERVICES HMI   LUM
   │      │      │      │
   ▼      ▼      ▼      ▼
Driver  Debug  Render  Source
issue   logs   issue   connect
        ON              issue
```

## RCA Decision Tree: Memory Issues

```
OOM/Crash Detected
       │
       ▼
┌────────────────────┐
│ Check memory trend │
└────────┬───────────┘
         │
    ┌────┴────┐
    ▼         ▼
Gradual    Sudden
increase   spike
    │         │
    ▼         ▼
Memory    Large
leak      allocation
    │         │
    ▼         ▼
Check     Check
delta     process
pattern   activity
```
